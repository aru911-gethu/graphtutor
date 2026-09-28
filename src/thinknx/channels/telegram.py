import asyncio
import random
from typing import Optional, List
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from thinknx.config import settings
from thinknx.graph.driver import get_driver
import thinknx.graph.queries as queries
from thinknx.learning.engine import LearningEngine, slugify
from thinknx.learning.mastery import FSRSMastery
from thinknx.learning.explainer import AdaptiveExplainer
from thinknx.learning.quiz import QuizGenerator
from thinknx.learning.paths import PathGenerator
from thinknx.ingest.router import IngestionRouter

logger = structlog.get_logger(__name__)


class TelegramBot:
    """
    Telegram Bot channel adapter for thinknx.
    Delivers micro-learning, quizzes, spaced repetition prompts, and launches
    the rich Telegram Mini App (TMA) for polymorphic visual cards.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        engine: Optional[LearningEngine] = None,
        ingest: Optional[IngestionRouter] = None,
        base_web_url: str = "http://localhost:8000"
    ):
        self.token = token or settings.telegram_bot_token
        self.driver = get_driver()
        self.engine = engine or LearningEngine(driver=self.driver)
        self.ingest = ingest or IngestionRouter()
        self.base_web_url = base_web_url.rstrip("/")

        self.app = None
        if self.token:
            self.app = Application.builder().token(self.token).build()
            self._register_handlers()

    def _register_handlers(self):
        if not self.app:
            return
        self.app.add_handler(CommandHandler("start", self.handle_start))
        self.app.add_handler(CommandHandler("learn", self.handle_learn))
        self.app.add_handler(CommandHandler("quiz", self.handle_quiz))
        self.app.add_handler(CommandHandler("progress", self.handle_progress))
        self.app.add_handler(CommandHandler("next", self.handle_next))
        self.app.add_handler(CommandHandler("path", self.handle_path))
        self.app.add_handler(CommandHandler("gaps", self.handle_gaps))
        self.app.add_handler(CommandHandler("help", self.handle_help))

        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User registers or re-engages with the bot."""
        user = update.effective_user
        user_id = f"telegram:{user.id}"

        async with self.driver.session() as session:
            await queries.create_user(session, user_id=user_id, name=user.first_name, platform="telegram")

        canvas_url = f"{self.base_web_url}/canvas/{user_id}"
        keyboard = [
            [InlineKeyboardButton("🚀 Explore Knowledge Canvas", web_app=WebAppInfo(url=canvas_url))],
            [InlineKeyboardButton("⚡ Learn Transformers", callback_data="learn:transformers")],
            [InlineKeyboardButton("🎯 View Suggested Next Topics", callback_data="cmd:next")],
        ]

        welcome_text = (
            f"👋 Welcome to *thinknx*, {user.first_name}!\n\n"
            "I'm your **Personal Adaptive Learning Agent**.\n"
            "I build an evolving knowledge graph of what you know, teach using concrete analogies and code remarks, and schedule review quizzes with FSRS spaced repetition.\n\n"
            "**Quick Commands:**\n"
            "• `/learn <topic>` — Learn any topic (e.g. `/learn transformers`)\n"
            "• `/quiz` — Spaced repetition review\n"
            "• `/progress` — View mastery and open your knowledge graph\n"
            "• `/next` — Discover concepts ready for your current level\n"
            "• `/path <goal>` — Roadmap to master a complex subject\n"
            "• Send photos of diagrams or voice notes anytime!"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_learn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User requests a lesson on a topic."""
        user_id = f"telegram:{update.effective_user.id}"
        topic = " ".join(context.args) if context.args else None

        if not topic:
            await update.message.reply_text(
                "Please specify a topic! Example:\n`/learn attention mechanism`\n`/learn docker`",
                parse_mode="Markdown"
            )
            return

        status_msg = await update.message.reply_text(f"🔍 Analyzing your knowledge graph for *{topic}*...", parse_mode="Markdown")

        try:
            result = await self.engine.teach(user_id, topic)
            payload = result["payload"]
            chat_markdown = result["chat_markdown"]
            concept_slug = slugify(topic)

            webapp_url = f"{self.base_web_url}/lesson/{concept_slug}?uid={user_id}&theme={payload.theme.value}"

            buttons = [
                [InlineKeyboardButton("📱 Open Visual Lesson & Code Remarks", web_app=WebAppInfo(url=webapp_url))]
            ]

            if result.get("quiz"):
                q0 = result["quiz"][0]
                options = list(q0["options"][:4])
                correct_answer = q0.get("correct_answer", options[0])
                random.shuffle(options)
                correct_idx = next((i for i, o in enumerate(options) if o == correct_answer), 0)
                buttons.append([
                    InlineKeyboardButton(f"A: {options[0][:24]}", callback_data=f"quiz:{concept_slug}:0:{correct_idx}"),
                    InlineKeyboardButton(f"B: {options[1][:24]}", callback_data=f"quiz:{concept_slug}:1:{correct_idx}"),
                ])

            summary_text = (
                f"🧠 *{payload.display_name}* `[{payload.theme.value.upper()}]`\n"
                f"Level: *{result['current_depth'].capitalize()}*\n\n"
                f"{chat_markdown[:400]}...\n\n"
                "💡 *Tap below to view full code snippets, remarks, and visual flow:*"
            )

            await status_msg.edit_text(
                summary_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error("Error executing /learn command", error=str(e))
            await status_msg.edit_text(f"Sorry, an error occurred while preparing your lesson: {e}")

    async def handle_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trigger due spaced repetition reviews."""
        user_id = f"telegram:{update.effective_user.id}"
        async with self.driver.session() as session:
            due = await queries.get_due_reviews(session, user_id, limit=5)

        if not due:
            await update.message.reply_text(
                "🎉 You're all caught up! No concepts due for review.\n"
                "Explore new concepts with `/learn <topic>` or `/next`.",
                parse_mode="Markdown"
            )
            return

        target = due[0]
        concept_name = target["concept"]
        display_name = target["displayName"]
        retrievability = float(target.get("retrievability", 0.8))

        quiz_list = await self.engine.quiz.generate(
            concept=display_name,
            level="working",
            count=1,
            mastery_context=f"Retrievability: {retrievability:.0%}"
        )
        q = quiz_list[0]
        options = list(q["options"][:4])
        correct_answer = q.get("correct_answer", options[0])
        random.shuffle(options)
        correct_idx = next((i for i, o in enumerate(options) if o == correct_answer), 0)

        keyboard = [
            [InlineKeyboardButton(f"{idx+1}. {opt}", callback_data=f"rev:{concept_name}:{idx}:{correct_idx}")]
            for idx, opt in enumerate(options)
        ]

        text = (
            f"⏰ *Spaced Review: {display_name}*\n"
            f"Recall Probability: `{retrievability:.0%}`\n\n"
            f"*{q['question']}*"
        )

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View user's learning stats and open the knowledge canvas."""
        user_id = f"telegram:{update.effective_user.id}"
        stats = await self.engine.get_progress(user_id)

        total = max(1, stats.get("totalConcepts", 0))
        mastered = stats.get("mastered", 0)
        in_prog = stats.get("inProgress", 0)
        gaps = stats.get("gaps", 0)
        reviews = stats.get("reviewsThisWeek", 0)

        pct = int((mastered / total) * 10)
        progress_bar = "█" * pct + "░" * (10 - pct)

        canvas_url = f"{self.base_web_url}/canvas/{user_id}"
        keyboard = [
            [InlineKeyboardButton("🌐 Open Interactive Knowledge Graph", web_app=WebAppInfo(url=canvas_url))],
            [InlineKeyboardButton("🔍 Review Weakest Gaps", callback_data="cmd:gaps")],
        ]

        text = (
            "📊 *Your Knowledge Dashboard*\n\n"
            f"• Mastered (≥80%): *{mastered}*\n"
            f"• In Progress: *{in_prog}*\n"
            f"• Knowledge Gaps (<30%): *{gaps}*\n"
            f"• Reviews this week: *{reviews}*\n\n"
            f"Mastery Progress: `[{progress_bar}]` {int((mastered/total)*100)}%\n\n"
            "Tap below to explore your personalized graph topology:"
        )

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_next(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recommendations whose prerequisites are satisfied."""
        user_id = f"telegram:{update.effective_user.id}"
        topics = await self.engine.get_next_topics(user_id, limit=5)

        if not topics:
            await update.message.reply_text("Start learning with `/learn <topic>` to unlock recommendations!")
            return

        keyboard = [
            [InlineKeyboardButton(f"⚡ {t['displayName']} ({t['domain']})", callback_data=f"learn:{t['concept']}")]
            for t in topics
        ]

        await update.message.reply_text(
            "🎯 *Recommended Next Concepts*\nYour prerequisites for these are satisfied:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_path(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compute ordered roadmap to a goal concept."""
        user_id = f"telegram:{update.effective_user.id}"
        goal = " ".join(context.args) if context.args else None

        if not goal:
            await update.message.reply_text("Please provide a goal topic! Example: `/path ai-agents`", parse_mode="Markdown")
            return

        roadmap = await self.engine.get_learning_path(user_id, goal)
        steps = roadmap.get("steps", [])

        if not steps:
            await update.message.reply_text(f"Goal *{goal}* is ready to learn! Use `/learn {goal}`", parse_mode="Markdown")
            return

        lines = [f"🗺️ *Learning Roadmap to {goal.title()}*\n"]
        for idx, s in enumerate(steps, 1):
            icon = "✅" if s["status"] == "mastered" else ("🔄" if s["status"] == "in_progress" else "🔒")
            lines.append(f"{icon} {idx}. *{s['displayName']}* ({s['depth'].capitalize()})")

        if roadmap.get("next_step"):
            next_name = roadmap["next_step"]["displayName"]
            next_slug = roadmap["next_step"]["concept"]
            keyboard = [[InlineKeyboardButton(f"Start Step: {next_name}", callback_data=f"learn:{next_slug}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = None

        await update.message.reply_text("\n".join(lines), reply_markup=reply_markup, parse_mode="Markdown")

    async def handle_gaps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List user's weakest concepts."""
        user_id = f"telegram:{update.effective_user.id}"
        async with self.driver.session() as session:
            gaps = await queries.get_knowledge_gaps(session, user_id, limit=5)

        if not gaps:
            await update.message.reply_text("✨ You have no critical knowledge gaps! Keep building with `/next`.")
            return

        keyboard = [
            [InlineKeyboardButton(f"Review {g['displayName']} ({int(g['mastery']*100)}%)", callback_data=f"learn:{g['concept']}")]
            for g in gaps
        ]

        await update.message.reply_text(
            "⚠️ *Your Top Knowledge Gaps*\nConcepts needing reinforcement:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show full help and command listings."""
        help_text = (
            "🤖 *thinknx Command Guide*\n\n"
            "• `/start` — Initialize your profile and knowledge graph\n"
            "• `/learn <topic>` — Learn a concept with interactive code remarks & visuals\n"
            "• `/quiz` — Review concepts due for spaced repetition\n"
            "• `/progress` — View learning metrics & interactive knowledge canvas\n"
            "• `/next` — Discover next topics with satisfied prerequisites\n"
            "• `/path <goal>` — Generate step-by-step roadmap to a goal\n"
            "• `/gaps` — Inspect your weakest concepts\n\n"
            "📸 *Multimodal Ingestion:*\n"
            "• Send photos of architecture diagrams or whiteboards\n"
            "• Send voice notes describing technical thoughts or lectures\n"
            "• Paste GitHub repository links or technical blog URLs"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process diagram or whiteboard photo."""
        user_id = f"telegram:{update.effective_user.id}"
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        status_msg = await update.message.reply_text("🖼️ Analyzing diagram and extracting concepts with Claude Vision...")
        try:
            result = await self.ingest.process_image(user_id, bytes(image_bytes))
            concepts = result.get("concepts", [])

            keyboard = [
                [InlineKeyboardButton(c["displayName"], callback_data=f"learn:{c['name']}")]
                for c in concepts[:4]
            ]

            text = (
                f"🔍 *I detected:*\n{result.get('description', '')}\n\n"
                f"💡 *Suggestion:* {result.get('suggested_learning', '')}\n\n"
                "Select a concept to begin learning:"
            )
            await status_msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error("Photo handling error", error=str(e))
            await status_msg.edit_text("Could not process image. Please try again.")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process voice note."""
        user_id = f"telegram:{update.effective_user.id}"
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        audio_bytes = await file.download_as_bytearray()

        status_msg = await update.message.reply_text("🎙️ Transcribing voice note with Whisper...")
        try:
            result = await self.ingest.process_audio(user_id, bytes(audio_bytes))
            concepts = result.get("concepts", [])

            keyboard = [
                [InlineKeyboardButton(c["displayName"], callback_data=f"learn:{c['name']}")]
                for c in concepts[:4]
            ]

            concept_bullets = "\n".join(f"• *{c['displayName']}*" for c in concepts)
            text = (
                f"📝 *Transcript:*\n_{result.get('transcript', '')}_\n\n"
                f"🧠 *Identified Concepts:*\n{concept_bullets}\n\n"
                "Which concept would you like to explore?"
            )
            await status_msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            logger.error("Voice handling error", error=str(e))
            await status_msg.edit_text("Could not transcribe voice note. Please try again.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle conversational queries and concept mentions."""
        user_id = f"telegram:{update.effective_user.id}"
        text = update.message.text.strip()

        # If it's a URL, route through URL ingestion
        if text.startswith("http://") or text.startswith("https://"):
            status_msg = await update.message.reply_text("🔗 Ingesting URL and analyzing concepts...")
            result = await self.ingest.process_url(user_id, text)
            concepts = result.get("concepts", [])
            keyboard = [[InlineKeyboardButton(c["displayName"], callback_data=f"learn:{c['name']}")] for c in concepts[:4]]
            await status_msg.edit_text(
                f"Extracted concepts from {text}:\n" + "\n".join(f"• {c['displayName']}" for c in concepts),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Regular concept extraction
        concepts = await self.ingest.process_text(user_id, text)
        if concepts:
            keyboard = [[InlineKeyboardButton(f"Learn {c['displayName']}", callback_data=f"learn:{c['name']}")] for c in concepts[:3]]
            await update.message.reply_text(
                f"I noticed you're exploring: {', '.join(c['displayName'] for c in concepts)}.\n"
                "Want to deep dive into any of them?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                "Not sure what to learn? Try `/learn <topic>`, `/quiz`, or send a diagram!",
                parse_mode="Markdown"
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button actions."""
        query = update.callback_query
        await query.answer()
        data = query.data
        user_id = f"telegram:{query.from_user.id}"

        if data.startswith("learn:"):
            concept = data.split(":", 1)[1]
            await query.edit_message_text(f"⏳ Generating adaptive lesson for *{concept.title()}*...", parse_mode="Markdown")
            result = await self.engine.teach(user_id, concept)
            payload = result["payload"]
            chat_markdown = result["chat_markdown"]
            webapp_url = f"{self.base_web_url}/lesson/{concept}?uid={user_id}&theme={payload.theme.value}"

            buttons = [
                [InlineKeyboardButton("📱 Open Visual Lesson & Remarks", web_app=WebAppInfo(url=webapp_url))]
            ]
            await query.edit_message_text(
                f"🧠 *{payload.display_name}*\n\n{chat_markdown[:350]}...\n\n_Tap below for code remarks and visual view:_",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown"
            )

        elif data.startswith("quiz:") or data.startswith("rev:"):
            parts = data.split(":")
            concept = parts[1]
            choice_idx = int(parts[2])
            correct_idx = int(parts[3]) if len(parts) > 3 else 0
            is_correct = choice_idx == correct_idx
            rating = 4 if is_correct else 1

            async with self.driver.session() as session:
                res = await self.engine.mastery.record_review(session, user_id, concept, rating=rating)

            status_icon = "✅" if is_correct else "⚠️"
            await query.edit_message_text(
                f"{status_icon} *Review Recorded!*\n\n"
                f"Concept: *{concept.title()}*\n"
                f"Updated Mastery: `{res['mastery']:.0%}` ({res['depth'].capitalize()} depth)\n"
                f"Recall Retrievability: `{res['retrievability']:.0%}`",
                parse_mode="Markdown"
            )

        elif data == "cmd:next":
            topics = await self.engine.get_next_topics(user_id, limit=4)
            keyboard = [[InlineKeyboardButton(t['displayName'], callback_data=f"learn:{t['concept']}")] for t in topics]
            await query.edit_message_text("🎯 *Recommended Topics:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

        elif data == "cmd:gaps":
            async with self.driver.session() as session:
                gaps = await queries.get_knowledge_gaps(session, user_id, limit=4)
            keyboard = [[InlineKeyboardButton(g['displayName'], callback_data=f"learn:{g['concept']}")] for g in gaps]
            await query.edit_message_text("⚠️ *Your Knowledge Gaps:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def run(self):
        """Start Telegram bot polling."""
        if not self.app:
            logger.warning("TELEGRAM_BOT_TOKEN not configured. Bot will not start polling.")
            return

        logger.info("Starting Telegram Bot with polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)


if __name__ == "__main__":
    bot = TelegramBot()
    asyncio.run(bot.run())
