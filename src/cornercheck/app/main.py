"""CornerCheck Slack app entrypoint (Socket Mode, no public URL needed)."""

import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from cornercheck.app.actions import register_actions
from cornercheck.app.assistant import assistant
from cornercheck.app.home import register_home
from cornercheck.config import get_settings

log = logging.getLogger("cornercheck.app")


def build_app() -> App:
    settings = get_settings()
    app = App(token=settings.slack_bot_token)
    app.use(assistant)
    register_actions(app)
    register_home(app)

    @app.error
    def on_unhandled_error(error: Exception, body: dict) -> None:
        # Last-resort net: Bolt's default handler only logs. Individual handlers post
        # their own fail-closed replies; this catches anything they miss.
        log.exception("unhandled listener error: %s", body.get("type"))

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    app = build_app()
    logging.getLogger("cornercheck").info(
        "CornerCheck starting (Socket Mode, model=%s)", settings.cornercheck_model
    )
    SocketModeHandler(app, settings.slack_app_token).start()


if __name__ == "__main__":
    main()
