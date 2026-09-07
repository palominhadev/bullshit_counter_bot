import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest

# Importar funções do banco de dados
from database import init_db, add_shit_record, get_today_count, get_all_records

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Inicializar banco de dados
init_db()


# --- Teclados ---

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Adicionar", callback_data="add_shit"),
            InlineKeyboardButton("📊 Total de hoje", callback_data="today_total"),
        ],
        [InlineKeyboardButton("❌ Sair", callback_data="exit_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_shit_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("💢 Fuck!", callback_data="shit_fuck"),
            InlineKeyboardButton("💢 Porr@!", callback_data="shit_porra"),
        ],
        [
            InlineKeyboardButton("💢 Merd@!", callback_data="shit_merda"),
            InlineKeyboardButton("💢 C@r@lh0!", callback_data="shit_caraio"),
        ],
        [InlineKeyboardButton("💢 Vai tomar no **", callback_data="shit_vai_tomar")],
        [InlineKeyboardButton("💢 Put@ que P@riu!", callback_data="shit_puta")],
        [InlineKeyboardButton("📝 Outros...", callback_data="shit_custom")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_after_register_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Registrar outro", callback_data="add_shit"),
            InlineKeyboardButton("⬅️ Menu principal", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="back_main")]]
    return InlineKeyboardMarkup(keyboard)


def get_exit_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("🔄 Abrir menu", callback_data="back_main")]]
    return InlineKeyboardMarkup(keyboard)


# --- Mapeamento de palavrões pré-definidos ---

PREDEFINED_SHITS = {
    "shit_fuck": "Fuck!",
    "shit_porra": "Porr@!",
    "shit_merda": "Merd@!",
    "shit_caraio": "C@r@lh0!",
    "shit_vai_tomar": "Vai tomar no **",
    "shit_puta": "Put@ que P@riu!",
}


# --- Funções auxiliares de envio ---

async def safe_reply_text(
    query_or_update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode: str = None
):
    """Envia mensagem com fallback de parse_mode (HTML -> MarkdownV2 -> plain)."""
    target = query_or_update.message if hasattr(query_or_update, "message") else query_or_update

    try:
        await target.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except BadRequest as e:
        logger.warning(f"Erro com {parse_mode}: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar: {e}")

    # Fallback MarkdownV2
    if parse_mode != "MarkdownV2":
        try:
            await target.reply_text(text, reply_markup=reply_markup, parse_mode="MarkdownV2")
            return
        except BadRequest as e:
            logger.warning(f"Erro com MarkdownV2: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar (MarkdownV2): {e}")

    # Fallback plain text
    try:
        await target.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Erro ao enviar sem formatação: {e}")


async def safe_edit_text(
    query, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode: str = None
):
    """Edita mensagem com fallback de parse_mode."""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except BadRequest as e:
        logger.warning(f"Erro ao editar com {parse_mode}: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao editar: {e}")

    if parse_mode != "MarkdownV2":
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="MarkdownV2")
            return
        except BadRequest as e:
            logger.warning(f"Erro ao editar com MarkdownV2: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao editar (MarkdownV2): {e}")

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Erro ao editar sem formatação: {e}")


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /start - mostra menu principal."""
    # Limpar estado de "aguardando input customizado"
    context.user_data.pop("waiting_custom_shit", None)

    text = "🤬 CONTADOR DE PALAVRÕES\n\nEscolha uma opção:"
    await safe_reply_text(update, text, get_main_menu_keyboard(), parse_mode="HTML")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal para todos os callbacks dos botões inline."""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest as e:
        logger.warning(f"Callback query inválida ou expirada: {e}")
        return

    callback_data = query.data
    logger.info(f"Callback recebido: {callback_data}")

    # Limpar estado de input customizado ao navegar
    if callback_data != "shit_custom":
        context.user_data.pop("waiting_custom_shit", None)

    # Menu principal
    if callback_data == "back_main":
        text = "🤬 CONTADOR DE PALAVRÕES\n\nEscolha uma opção:"
        await safe_edit_text(query, text, get_main_menu_keyboard(), parse_mode="HTML")
        return

    # Submenu "Adicionar palavrão"
    if callback_data == "add_shit":
        text = "🤬 ADICIONAR PALAVRÃO\n\nEscolha uma opção:"
        await safe_edit_text(query, text, get_add_shit_keyboard(), parse_mode="HTML")
        return

    # Palavrões pré-definidos
    if callback_data in PREDEFINED_SHITS:
        shit_text = PREDEFINED_SHITS[callback_data]
        record = add_shit_record(shit_text)

        time_str = record["datetime"].strftime("%H:%M:%S")
        text = f"✅ Palavrão registrado!\n\n🤬 {record['shit']}\n🕐 {time_str}"
        await safe_edit_text(query, text, get_after_register_keyboard(), parse_mode="HTML")
        return

    # Opção "Outros..." - solicita input do usuário
    if callback_data == "shit_custom":
        context.user_data["waiting_custom_shit"] = True
        text = "📝 OUTROS\n\nDigite o palavrão que deseja registrar:"
        await safe_edit_text(query, text, get_back_main_keyboard(), parse_mode="HTML")
        return

    # Total de hoje
    if callback_data == "today_total":
        count = get_today_count()
        today_str = datetime.now().strftime("%d/%m/%Y")
        text = f"📊 PALAVRÕES DE HOJE\n\n🤬 Total registrado: {count}\n📅 {today_str}"
        await safe_edit_text(query, text, get_back_main_keyboard(), parse_mode="HTML")
        return

    # Sair
    if callback_data == "exit_menu":
        text = "👋 Até mais!\n\nUse /start para abrir o contador novamente."
        await safe_edit_text(query, text, get_exit_keyboard(), parse_mode="HTML")
        return

    # Callback desconhecido
    logger.warning(f"Callback desconhecido: {callback_data}")
    await safe_edit_text(
        query,
        "Opção inválida. Por favor, escolha uma opção válida.",
        get_main_menu_keyboard(),
        parse_mode="HTML",
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto (usado para 'Outros...')."""
    # Verifica se está aguardando input customizado
    if not context.user_data.get("waiting_custom_shit"):
        # Não está no fluxo de input customizado, ignora ou responde ao /start
        return

    # Limpar o estado
    context.user_data.pop("waiting_custom_shit", None)

    shit_text = update.message.text.strip()
    if not shit_text:
        await safe_reply_text(
            update,
            "❌ Texto vazio. Tente novamente.",
            get_add_shit_keyboard(),
            parse_mode="HTML",
        )
        return

    record = add_shit_record(shit_text)
    time_str = record["datetime"].strftime("%H:%M:%S")
    text = f"✅ Palavrão registrado!\n\n🤬 {record['shit']}\n🕐 {time_str}"
    await safe_reply_text(update, text, get_after_register_keyboard(), parse_mode="HTML")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros."""
    logger.error(f"Erro não tratado: {context.error}", exc_info=context.error)


def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN não encontrado no arquivo .env")
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")

    logger.info("Iniciando Contador de Palavrões...")

    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(handle_callback))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
        )
        application.add_error_handler(error_handler)

        logger.info("🤖 Bot iniciado com sucesso! Pressione Ctrl+C para parar.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Erro ao iniciar bot: {e}")
        raise


if __name__ == "__main__":
    main()