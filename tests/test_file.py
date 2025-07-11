import platform
import tempfile
import unittest
from pathlib import Path

from panther._utils import detect_mime_type
from panther.file_handler import File


class TestFile(unittest.TestCase):
    def test_file_init_with_bytes(self):
        data = b'hello world'
        f = File(file_name='test.txt', content_type='text/plain', file=data)
        assert f.file_name == 'test.txt'
        assert f.content_type == 'text/plain'
        assert f.file == data
        assert f.size == len(data)

    def test_file_init_with_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'foo.txt'
            file_path.write_bytes(b'abc123')
            f = File(file_name=str(file_path), content_type='text/plain')
            assert f.file_name == str(file_path)
            assert f.content_type == 'text/plain'
            assert f.size == 6

    def test_file_read_and_seek(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'bar.txt'
            file_path.write_bytes(b'abcdef')
            f = File(file_name=str(file_path), content_type='text/plain')
            with f:
                assert f.read(3) == b'abc'
                assert f.tell() == 3
                f.seek(0)
                assert f.read() == b'abcdef'

    def test_file_write_in_memory(self):
        f = File(file_name='baz.txt', content_type='text/plain', file=b'foo')
        f.write(b'bar')
        assert f.file == b'foobar'
        assert f.size == 6

    def test_file_write_on_disk_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'baz.txt'
            file_path.write_bytes(b'foo')
            f = File(file_name=str(file_path), content_type='text/plain')
            with f:
                try:
                    f.write(b'bar')
                    assert False, 'Expected IOError to be raised'
                except IOError:
                    pass

    def test_file_save_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='test.txt', content_type='text/plain', file=b'data')
            save_path = Path(tmp_dir_name) / 'out.txt'
            result_path = f.save(str(save_path), overwrite=True)
            assert Path(result_path).read_bytes() == b'data'
            # Overwrite again
            f2 = File(file_name='test.txt', content_type='text/plain', file=b'new')
            result_path2 = f2.save(str(save_path), overwrite=True)
            assert Path(result_path2).read_bytes() == b'new'
            assert result_path == result_path2

    def test_file_save_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='test.txt', content_type='text/plain', file=b'data')
            save_path = Path(tmp_dir_name) / 'out.txt'
            result_path1 = f.save(str(save_path), overwrite=False)
            assert Path(result_path1).read_bytes() == b'data'
            # Save again, should create a new file with timestamp
            f2 = File(file_name='test.txt', content_type='text/plain', file=b'new')
            result_path2 = f2.save(str(save_path), overwrite=False)
            assert Path(result_path2).read_bytes() == b'new'
            assert result_path1 != result_path2

    def test_file_save_idempotent(self):
        """Test that save() method is idempotent - returns same path on multiple calls"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='test.txt', content_type='text/plain', file=b'data')
            save_path = Path(tmp_dir_name) / 'out.txt'

            # First call
            result_path1 = f.save(str(save_path), overwrite=True)
            assert Path(result_path1).read_bytes() == b'data'

            # Second call - should return same path
            result_path2 = f.save(str(save_path), overwrite=True)
            assert result_path1 == result_path2

            # Third call - should return same path
            result_path3 = f.save(str(save_path), overwrite=True)
            assert result_path1 == result_path3

            # Verify file content is still the same
            assert Path(result_path1).read_bytes() == b'data'

    def test_file_save_idempotent_with_different_paths(self):
        """Test that idempotency works even when called with different paths"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='test.txt', content_type='text/plain', file=b'data')

            # First call
            result_path1 = f.save(Path(tmp_dir_name) / 'first.txt', overwrite=True)

            # Second call with different path - should still return first path
            result_path2 = f.save(Path(tmp_dir_name) / 'second.txt', overwrite=True)
            assert result_path1 == result_path2

            # Third call with no path - should still return first path
            result_path3 = f.save(overwrite=True)
            assert result_path1 == result_path3

    def test_file_save_directory_path(self):
        """Test saving to directory path (ending with /)"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='document.pdf', content_type='application/pdf', file=b'pdf content')

            # Save to directory
            result_path = f.save(f'{tmp_dir_name}/uploads/')
            expected_path = Path(tmp_dir_name) / 'uploads' / 'document.pdf'

            assert result_path == str(expected_path)
            assert expected_path.exists()
            assert expected_path.read_bytes() == b'pdf content'

    def test_file_save_nested_directory_path(self):
        """Test saving to nested directory path"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='image.jpg', content_type='image/jpeg', file=b'jpeg content')

            # Save to nested directory
            result_path = f.save(f'{tmp_dir_name}/uploads/images/')
            expected_path = Path(tmp_dir_name) / 'uploads' / 'images' / 'image.jpg'

            assert result_path == str(expected_path)
            assert expected_path.exists()
            assert expected_path.read_bytes() == b'jpeg content'

    def test_file_save_directory_path_with_custom_filename(self):
        """Test saving to directory with custom filename"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='original.txt', content_type='text/plain', file=b'content')

            # Save to directory with custom filename
            result_path = f.save(f'{tmp_dir_name}/uploads/custom_name.txt')
            expected_path = Path(tmp_dir_name) / 'uploads' / 'custom_name.txt'

            assert result_path == str(expected_path)
            assert expected_path.exists()
            assert expected_path.read_bytes() == b'content'

    def test_file_save_directory_creation(self):
        """Test that directories are created automatically"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='test.txt', content_type='text/plain', file=b'data')

            # Try to save to non-existent directory
            target_dir = Path(tmp_dir_name) / 'new' / 'nested' / 'directory'
            result_path = f.save(str(target_dir / 'test.txt'), overwrite=True)

            # Directory should be created
            assert target_dir.exists()
            assert Path(result_path).exists()

    def test_file_save_directory_path_idempotent(self):
        """Test that directory path saving is also idempotent"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            f = File(file_name='test.txt', content_type='text/plain', file=b'data')

            # First call
            result_path1 = f.save(f'{tmp_dir_name}/uploads/')

            # Second call - should return same path
            result_path2 = f.save(f'{tmp_dir_name}/uploads/')
            assert result_path1 == result_path2

            # Third call with different directory - should still return first path
            result_path3 = f.save(f'{tmp_dir_name}/different/')
            assert result_path1 == result_path3

    def test_file_save_without_path_uses_filename(self):
        """Test that save() without path uses the original filename"""
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            original_cwd = Path.cwd()
            try:
                # Change to temp directory for testing
                import os

                os.chdir(tmp_dir_name)

                f = File(file_name='test.txt', content_type='text/plain', file=b'data')
                result_path = f.save()

                # Should save as 'test.txt' in current directory
                expected_path = Path(tmp_dir_name) / 'test.txt'
                assert Path(result_path).resolve() == expected_path.resolve()
                assert Path(result_path).exists()

            finally:
                os.chdir(original_cwd)

    def test_file_repr_and_str(self):
        f = File(file_name='foo.txt', content_type='text/plain', file=b'bar')
        s = str(f)
        assert 'foo.txt' in s
        assert 'text/plain' in s

    def test_file_ensure_buffer_error(self):
        f = File(file_name='foo.txt', content_type='text/plain')
        f.file = None
        f._file_path = None
        f._buffer = None
        try:
            f._ensure_buffer()
            assert False, 'Expected ValueError to be raised'
        except ValueError:
            pass


class TestDetectMimeType(unittest.TestCase):
    def test_extension_based_detection(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'foo.txt'
            file_path.write_text('hello')
            assert detect_mime_type(str(file_path)) == 'text/plain'

    def test_png_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'img.png'
            file_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'rest')
            assert detect_mime_type(str(file_path)) == 'image/png'

    def test_pdf_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'doc.pdf'
            file_path.write_bytes(b'%PDF-1.4 some pdf data')
            assert detect_mime_type(str(file_path)) == 'application/pdf'

    def test_zip_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'archive.zip'
            file_path.write_bytes(b'PK\x03\x04rest')
            if platform.system() == 'Windows':
                assert detect_mime_type(str(file_path)) == 'application/x-zip-compressed'
            else:
                assert detect_mime_type(str(file_path)) == 'application/zip'

    def test_jpeg_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'img.jpg'
            file_path.write_bytes(b'\xff\xd8\xffrest')
            assert detect_mime_type(str(file_path)) == 'image/jpeg'

    def test_gif_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'img.gif'
            file_path.write_bytes(b'GIF89a rest')
            assert detect_mime_type(str(file_path)) == 'image/gif'

    def test_bmp_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'img.bmp'
            file_path.write_bytes(b'BMrest')
            assert detect_mime_type(str(file_path)) == 'image/bmp'

    def test_ico_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'icon'
            file_path.write_bytes(b'\x00\x00\x01\x00rest')
            assert detect_mime_type(str(file_path)) == 'image/x-icon'

    def test_tiff_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'img.tiff'
            file_path.write_bytes(b'II*\x00rest')
            assert detect_mime_type(str(file_path)) == 'image/tiff'

    def test_mp4_magic_number(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'video.mp4'
            file_path.write_bytes(b'\x00\x00\x00\x18ftyprest')
            assert detect_mime_type(str(file_path)) == 'video/mp4'

    def test_fallback_octet_stream(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_path = Path(tmp_dir_name) / 'unknown.bin'
            file_path.write_bytes(b'randomdata123456')
            assert detect_mime_type(str(file_path)) == 'application/octet-stream'
