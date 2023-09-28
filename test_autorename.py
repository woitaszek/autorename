# Source Generated with Decompyle++
# File: test_autorename.cpython-39.pyc (Python 3.9)

import os
import sys
import unittest
import unittest.mock as unittest
import autorename
OS_STAT_RESULT = os.stat_result([
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    1262430245,
    0])
MOCK_OPEN_EMPTY = unittest.mock.mock_open(b'', **('read_data',))

def TestAutoRename():
    '''TestAutoRename'''
    
    def setUp(self = None):
        return super().setUp()

    
    def test_rename_filename_png(self, mock_os_rename, *args):
        '''
        Test renaming a file that matches an expected suffix: /path/does/not/exist/filename.png
        '''
        sys.stderr.write('\n')
        new_name = autorename.auto_name_file('/path/does/not/exist', 'filename.png', False, **('dryrun',))
        self.assertEqual(new_name, '2010-01-02-d41d8cd98f.png')
        mock_os_rename.assert_called_with('/path/does/not/exist/filename.png', '/path/does/not/exist/2010-01-02-d41d8cd98f.png')

    test_rename_filename_png = unittest.mock.patch('builtins.open', MOCK_OPEN_EMPTY)(unittest.mock.patch('os.stat', OS_STAT_RESULT, **('return_value',))(unittest.mock.patch('os.rename')(test_rename_filename_png)))
    
    def test_rename_filename_hash_png(self, mock_os_rename, *args):
        '''
        Test renaming a file that matches an expected suffix with a changed hash: /path/does/not/exist/filename-HASH.png
        '''
        sys.stderr.write('\n')
        new_name = autorename.auto_name_file('/path/does/not/exist', 'filename.png', False, **('dryrun',))
        self.assertEqual(new_name, '2010-01-02-d41d8cd98f.png')
        mock_os_rename.assert_called_with('/path/does/not/exist/filename.png', '/path/does/not/exist/2010-01-02-d41d8cd98f.png')

    test_rename_filename_hash_png = unittest.mock.patch('builtins.open', MOCK_OPEN_EMPTY)(unittest.mock.patch('os.stat', OS_STAT_RESULT, **('return_value',))(unittest.mock.patch('os.rename')(test_rename_filename_hash_png)))
    
    def test_skip_filename_dat(self, mock_os_rename, *args):
        '''
        Test skipping a file that has an unexpected suffix: /path/does/not/exist/filename.dat
        '''
        sys.stderr.write('\n')
        new_name = autorename.auto_name_file('/path/does/not/exist', 'filename.dat', False, **('dryrun',))
        self.assertIsNone(new_name)
        mock_os_rename.assert_not_called()

    test_skip_filename_dat = unittest.mock.patch('builtins.open', MOCK_OPEN_EMPTY)(unittest.mock.patch('os.stat', OS_STAT_RESULT, **('return_value',))(unittest.mock.patch('os.rename')(test_skip_filename_dat)))
    
    def test_skip_filename_prefix(self, mock_os_rename, *args):
        '''
        Test skipping files that start with yyyy-mm-dd as a prefix followed by a space
        '''
        sys.stderr.write('\n')
        for filename in ('2022-01-01 filename.png', '2022-01-XX filename.png'):
            new_name = autorename.auto_name_file('/path/does/not/exist', filename, False, **('dryrun',))
            self.assertIsNone(new_name)
            mock_os_rename.assert_not_called()

    test_skip_filename_prefix = unittest.mock.patch('builtins.open', MOCK_OPEN_EMPTY)(unittest.mock.patch('os.stat', OS_STAT_RESULT, **('return_value',))(unittest.mock.patch('os.rename')(test_skip_filename_prefix)))
    __classcell__ = None

TestAutoRename = <NODE:27>(TestAutoRename, 'TestAutoRename', unittest.TestCase)
if __name__ == '__main__':
    unittest.main()
