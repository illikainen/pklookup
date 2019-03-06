import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pklookup import cli, www


class CliTest(TestCase):
    def test_no_url(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      admin_token = abcd\n
                      """)
            tmp.flush()

            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "token",
                "add"
            ])
            self.assertNotEqual(result.exit_code, 0)

    @patch("getpass.getpass")  # type: ignore
    def test_no_token(self, mock: MagicMock) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      url = https://url\n
                      """)
            tmp.flush()

            runner = CliRunner()
            runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "token",
                "add"
            ])
            self.assertEqual(mock.call_count, 1)


class AddTokenTest(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.config.write(b"""
                          [pklookup]\n
                           url = https://url:port\n
                           admin_token = abcd\n
                           """)
        self.config.flush()

    def tearDown(self) -> None:
        self.config.close()

    def test_no_role(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.token_add)
        self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_invalid_role(self, mock: MagicMock) -> None:
        mock.return_value = {"token": "123"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "add"
            "--role=xyz",
            "--description=desc",
        ])
        self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        mock.side_effect = www.WWWError

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "add",
            "--role=server",
            "--description=desc",
        ])
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_success_admin(self, mock: MagicMock) -> None:
        mock.return_value = {"token": "xyz"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "add",
            "--role=admin",
            "--description=desc",
        ])

        args, kwargs = mock.call_args
        self.assertEqual(args, ("token",))
        self.assertEqual(kwargs, {"role": "admin", "description": "desc"})
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("xyz" in result.output)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_success_server(self, mock: MagicMock) -> None:
        mock.return_value = {"token": "abcd"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "add",
            "--role=server",
            "--description=desc",
        ])

        args, kwargs = mock.call_args
        self.assertEqual(args, ("token",))
        self.assertEqual(kwargs, {"role": "server", "description": "desc"})
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("abcd" in result.output)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_invalid_type(self, mock: MagicMock) -> None:
        mock.return_value = "abcd"

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "add",
            "--role=admin",
        ])
        self.assertTrue("invalid response" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_missing_token(self, mock: MagicMock) -> None:
        mock.return_value = {"token123": "abcd"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "add",
            "--role=admin",
        ])
        self.assertTrue("invalid response" in result.output)
        self.assertEqual(result.exit_code, 1)


class DeleteTokenTest(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.config.write(b"""
                          [pklookup]\n
                           url = https://url:port\n
                           admin_token = abcd\n
                           """)
        self.config.flush()

    def tearDown(self) -> None:
        self.config.close()

    def test_no_id(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.token_delete)
        self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.WWW.delete")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        mock.side_effect = www.WWWError("msg")

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "delete",
            "--id=1",
        ])
        self.assertEqual(result.output, "ERROR: msg\n")
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.delete")  # type: ignore
    def test_success(self, mock: MagicMock) -> None:
        mock.return_value = {"message": "xyz"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "delete",
            "--id=1"
        ])

        args, kwargs = mock.call_args
        self.assertEqual(args, ("token",))
        self.assertEqual(kwargs, {"id": 1})
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("xyz" in result.output)

    @patch("pklookup.www.WWW.delete")  # type: ignore
    def test_invalid_type(self, mock: MagicMock) -> None:
        mock.return_value = "abcd"

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "delete",
            "--id=1",
        ])
        self.assertTrue("invalid response" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.delete")  # type: ignore
    def test_missing_message(self, mock: MagicMock) -> None:
        mock.return_value = {"message123": "abcd"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "delete",
            "--id=1",
        ])
        self.assertTrue("invalid response" in result.output)
        self.assertEqual(result.exit_code, 1)


class ListTokenTest(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.config.write(b"""
                          [pklookup]\n
                           url = https://url:port\n
                           admin_token = abcd\n
                           """)
        self.config.flush()

    def tearDown(self) -> None:
        self.config.close()

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_invalid_type(self, mock: MagicMock) -> None:
        mock.return_value = "abcd"

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "list"
        ])
        self.assertTrue("invalid token list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_tokens(self, mock: MagicMock) -> None:
        mock.return_value = {"abc": [{
            "id": 0,
            "role": "x",
            "description": "y",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "list"
        ])
        self.assertTrue("invalid token list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_id_field(self, mock: MagicMock) -> None:
        mock.return_value = {"tokens": [{
            "role": "x",
            "description": "y",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "list"
        ])
        self.assertTrue("invalid token list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        mock.side_effect = www.WWWError

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "list"
        ])
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_success(self, mock: MagicMock) -> None:
        mock.return_value = {"tokens": [{
            "id": "1234",
            "role": "rrrrr",
            "description": "ddddd",
            "created": "cccc"
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "token",
            "list"
        ])

        for key, value in mock.return_value["tokens"][0].items():
            self.assertTrue(key in result.output)
            self.assertTrue(value in result.output)

        self.assertEqual(result.exit_code, 0)


class AddServerTest(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.config.write(b"""
                          [pklookup]\n
                           url = https://url:port\n
                           admin_token = abcd\n
                           """)
        self.config.flush()

    def tearDown(self) -> None:
        self.config.close()

    def test_no_public_key(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.server_add)
        self.assertNotEqual(result.exit_code, 0)

    def test_public_key_not_found(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            pass

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "add",
            "--public-key=@{}".format(tmp.name),
        ])
        self.assertTrue("No such file or directory" in result.output)
        self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        mock.side_effect = www.WWWError("errmsg")

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "add",
            "--public-key=asdf",
        ])
        self.assertTrue("errmsg" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_success_arg(self, mock: MagicMock) -> None:
        mock.return_value = {"message": "xyz"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "add",
            "--public-key=asdf",
        ])

        args, kwargs = mock.call_args
        self.assertEqual(args, ("server",))
        self.assertEqual(kwargs, {"public_key": "asdf"})
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("xyz" in result.output)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_success_file(self, mock: MagicMock) -> None:
        mock.return_value = {"message": "xyz"}

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"  first line\n second line\n")
            tmp.flush()

            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                self.config.name,
                "server",
                "add",
                "--public-key=@{}".format(tmp.name),
            ])

        args, kwargs = mock.call_args
        self.assertEqual(args, ("server",))
        self.assertEqual(kwargs, {"public_key": "first line"})
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("xyz" in result.output)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_invalid_type(self, mock: MagicMock) -> None:
        mock.return_value = "abcd"

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "add",
            "--public-key=asdf",
        ])
        self.assertTrue("invalid response" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.post")  # type: ignore
    def test_missing_message(self, mock: MagicMock) -> None:
        mock.return_value = {"msg123": "abcd"}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "add",
            "--public-key=asdf",
        ])
        self.assertTrue("invalid response" in result.output)
        self.assertEqual(result.exit_code, 1)


class ListServerTest(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.config.write(b"""
                          [pklookup]\n
                           url = https://url:port\n
                           admin_token = abcd\n
                           """)
        self.config.flush()

    def tearDown(self) -> None:
        self.config.close()

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_invalid_type(self, mock: MagicMock) -> None:
        mock.return_value = "abcd"

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "list"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_servers(self, mock: MagicMock) -> None:
        mock.return_value = {"abc": [{
            "id": 0,
            "token_id": "1",
            "ip": "1.2.3.4",
            "port": "1234",
            "key_type": "rsa",
            "public_key": "...",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "list"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_id_field(self, mock: MagicMock) -> None:
        mock.return_value = {"servers": [{
            "token_id": "1",
            "ip": "1.2.3.4",
            "port": "1234",
            "key_type": "rsa",
            "public_key": "...",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "list"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        mock.side_effect = www.WWWError

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "list"
        ])
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_success(self, mock: MagicMock) -> None:
        mock.return_value = {"servers": [{
            "id": "0",
            "token_id": "1",
            "ip": "1.2.3.4",
            "port": "1234",
            "key_type": "rsa",
            "key_data": "...",
            "key_comment": "xyz",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "list"
        ])

        for key, value in mock.return_value["servers"][0].items():
            self.assertTrue(key in result.output)
            self.assertTrue(value in result.output)

        self.assertEqual(result.exit_code, 0)


class SaveKeyTest(TestCase):
    def setUp(self) -> None:
        self.config = tempfile.NamedTemporaryFile()
        self.known_hosts = tempfile.NamedTemporaryFile()
        self.config.write("""
                          [pklookup]\n
                          url = https://url:port\n
                          admin_token = abcd\n
                          known_hosts = {}\n
                          """.format(self.known_hosts.name).encode("utf-8"))
        self.config.flush()

    def tearDown(self) -> None:
        self.config.close()
        self.known_hosts.close()

    def test_missing_id(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
        ])
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_id(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=asdf"
        ])
        self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_invalid_type(self, mock: MagicMock) -> None:
        mock.return_value = "abcd"

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_servers(self, mock: MagicMock) -> None:
        mock.return_value = {"abc": [{
            "id": 0,
            "token_id": "1",
            "ip": "1.2.3.4",
            "port": "1234",
            "key_type": "rsa",
            "public_key": "...",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_ip_field(self, mock: MagicMock) -> None:
        mock.return_value = {"servers": [{
            "id": "0",
            "token_id": "1",
            "port": "1234",
            "key_type": "rsa",
            "public_key": "...",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_missing_public_key_field(self, mock: MagicMock) -> None:
        mock.return_value = {"servers": [{
            "id": "0",
            "token_id": "1",
            "ip": "1.2.3.4",
            "port": "1234",
            "key_type": "rsa",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])
        self.assertTrue("invalid server list" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_empty_servers(self, mock: MagicMock) -> None:
        mock.return_value = {"servers": []}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])
        self.assertTrue("invalid server id" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        mock.side_effect = www.WWWError("errmsg")

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])
        self.assertTrue("errmsg" in result.output)
        self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.WWW.get")  # type: ignore
    def test_success(self, mock: MagicMock) -> None:
        mock.return_value = {"servers": [{
            "id": "0",
            "token_id": "1",
            "ip": "1.2.3.4",
            "port": "1234",
            "key_type": "ssh-rsa",
            "key_data": "data",
            "key_comment": "comment",
            "created": "..."
        }]}

        runner = CliRunner()
        result = runner.invoke(cli.cli, [
            "--config-file",
            self.config.name,
            "server",
            "save-key",
            "--id=0"
        ])

        self.assertEqual(self.known_hosts.read(),
                         b"1.2.3.4 ssh-rsa data\n")
        self.assertEqual(result.exit_code, 0)
