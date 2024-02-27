from datetime import timedelta
from pathlib import Path

from typer.testing import CliRunner

from sud.cli import app
from sud.config import Config, TelegramConfig
from sud.updater import Updater

runner = CliRunner()


def test_version(mocker):
    mocker.patch("sud.cli.get_version", return_value="x.y.z")
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "x.y.z" in result.stdout


def test_run(mocker):
    m_cfg_ctor = mocker.patch("sud.cli.Config")
    m_run = mocker.patch.object(Updater, "run")

    result = runner.invoke(app, ["--config-file", "/my/config.yml", "run"])
    assert result.exit_code == 0
    m_cfg_ctor.assert_called_once_with(Path("/my/config.yml"))
    m_run.assert_called_once()


def test_init(mocker):
    m_cfg_load = mocker.patch.object(Config, "load")
    m_cfg_store = mocker.patch.object(Config, "store")

    config = Config("/etc/sud/sud-config.yml")

    m_cfg_ctor = mocker.patch("sud.cli.Config", return_value=config)

    result = runner.invoke(
        app,
        [
            "init",
            "--hostname",
            "my.host.name",
            "--api-secret",
            "super-duper-secret",
            "--frequency",
            "600",
            "--telegram-notifications",
            "-1234",
            "tg-token",
        ],
    )
    assert result.exit_code == 0
    m_cfg_ctor.assert_called_once_with(Path("/etc/sud/sud-config.yml"))
    m_cfg_load.assert_not_called()
    m_cfg_store.assert_called_once()
    assert config.hostname == "my.host.name"
    assert config.api_secret == "super-duper-secret"
    assert config.frequency == timedelta(seconds=600)
    assert config.telegram == TelegramConfig(-1234, "tg-token")


def test_init_prompt(mocker):
    m_cfg_load = mocker.patch.object(Config, "load")
    m_cfg_store = mocker.patch.object(Config, "store")

    config = Config("/etc/sud/sud-config.yml")

    m_cfg_ctor = mocker.patch("sud.cli.Config", return_value=config)
    mocker.patch(
        "sud.cli.HostnamePrompt.ask",
        return_value="my.host.name",
    )

    m_prompt_secret = mocker.patch(
        "sud.cli.APISecretPrompt.ask",
        return_value="super-duper-secret",
    )

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    m_cfg_ctor.assert_called_once_with(Path("/etc/sud/sud-config.yml"))
    m_cfg_load.assert_not_called()
    m_cfg_store.assert_called_once()
    m_prompt_secret.assert_called_once_with(mocker.ANY, password=True)
    assert config.hostname == "my.host.name"
    assert config.api_secret == "super-duper-secret"
    assert config.frequency == timedelta(seconds=300)
    assert config.telegram is None


def test_init_invalid_frequency(mocker):
    mocker.patch.object(Config, "load")
    mocker.patch.object(Config, "store")

    config = Config("/etc/sud/sud-config.yml")

    mocker.patch("sud.cli.Config", return_value=config)

    result = runner.invoke(
        app,
        [
            "init",
            "--hostname",
            "my.host.name",
            "--api-secret",
            "super-duper-secret",
            "--frequency",
            "1",
        ],
    )
    assert result.exit_code != 0
    assert "Minimum frequency is once per" in result.stdout
    assert "minutes (60 seconds)." in result.stdout
