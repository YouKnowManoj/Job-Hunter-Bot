import os
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

def get_connection():
    return psycopg2.connect(
        host="postgres",
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

# --------------------
# COMMANDS
# --------------------

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs;")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM jobs WHERE applied = TRUE;")
    applied = cur.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        f"📊 Stats\nTotal: {total}\nApplied: {applied}\nPending: {total - applied}"
    )

async def list_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, company, match_score
        FROM jobs
        ORDER BY scraped_at DESC
        LIMIT 5;
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No jobs found.")
        return

    message = "📝 Recent Jobs:\n\n"
    for row in rows:
        message += f"ID: {row[0]}\n{row[1]} @ {row[2]}\nScore: {row[3]}\n\n"

    await update.message.reply_text(message)

async def unapplied(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, company
        FROM jobs
        WHERE applied = FALSE
        ORDER BY scraped_at DESC
        LIMIT 5;
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No pending jobs.")
        return

    message = "🚀 Unapplied Jobs:\n\n"
    for row in rows:
        message += f"ID: {row[0]} | {row[1]} @ {row[2]}\n"

    await update.message.reply_text(message)

async def apply_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /apply <job_id>")
        return

    job_id = context.args[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE jobs SET applied = TRUE WHERE id = %s;", (job_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Marked job {job_id} as applied.")

# --------------------
# START BOT
# --------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("list", list_jobs))
app.add_handler(CommandHandler("unapplied", unapplied))
app.add_handler(CommandHandler("apply", apply_job))

print("Bot started...")
app.run_polling()
