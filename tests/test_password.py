import pytest
from mock import sentinel, patch, call

import jirafs.password
from jirafs.password import get_password_from_login_data


class TestGetPasswordFromLoginData(object):
    def test_should_return_cached_password(self):
        jirafs.password.password = sentinel.PASSWORD
        assert sentinel.PASSWORD == get_password_from_login_data({})

    def test_should_return_cached_password_and_remove_login_password(self):
        jirafs.password.password = sentinel.PASSWORD
        login_data = {'password': sentinel.LOGIN_PASSWORD}
        assert sentinel.PASSWORD == get_password_from_login_data(login_data)
        assert 'password' not in login_data

    def test_should_return_plain_text_password_if_no_password_cached_and_no_password_encrypted_flag(self):
        jirafs.password.password = None
        login_data = {'password': sentinel.LOGIN_PASSWORD}
        assert sentinel.LOGIN_PASSWORD == get_password_from_login_data(login_data)
        assert 'password' not in login_data

    def test_should_return_plain_text_password_if_no_password_cached_and_password_encrypted_flag_set_to_false(self):
        jirafs.password.password = None
        login_data = {'password': sentinel.LOGIN_PASSWORD, 'password_encrypted': False}
        assert sentinel.LOGIN_PASSWORD == get_password_from_login_data(login_data)
        assert 'password' not in login_data

    @patch('jirafs.password.scrypt')
    @patch('jirafs.utils.get_user_input')
    def test_should_return_decrypted_password_if_password_encrypted_flag_is_set(
            self, mock_get_user_input,  mock_scrypt):
        mock_scrypt.decrypt.return_value = sentinel.DECRYPTED_PASSWORD
        mock_get_user_input.return_value = sentinel.PASSPHRASE
        jirafs.password.password = None
        login_data = {'password': sentinel.LOGIN_PASSWORD, 'password_encrypted': True}
        assert sentinel.DECRYPTED_PASSWORD == get_password_from_login_data(login_data)
        assert 'password' not in login_data
        assert [call(sentinel.LOGIN_PASSWORD, sentinel.PASSPHRASE)] == mock_scrypt.decrypt.call_args_list

    @patch('jirafs.password.scrypt')
    @patch('jirafs.utils.get_user_input')
    def test_should_raise_error_if_exception_encountered_during_decryption(
            self, mock_get_user_input,  mock_scrypt):
        mock_scrypt.decrypt.side_effect = Exception
        mock_get_user_input.return_value = sentinel.PASSPHRASE
        jirafs.password.password = None
        login_data = {'password': sentinel.LOGIN_PASSWORD, 'password_encrypted': True}
        with pytest.raises(ValueError):
            get_password_from_login_data(login_data)
        assert 'password' not in login_data
        assert [call(sentinel.LOGIN_PASSWORD, sentinel.PASSPHRASE)] == mock_scrypt.decrypt.call_args_list
