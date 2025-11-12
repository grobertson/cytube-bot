"""
Unit tests for lib/media_link.py

Tests MediaLink class for URL parsing and conversion across 24+ media providers.
"""
import pytest
from unittest.mock import patch
from lib.media_link import MediaLink


class TestMediaLinkInit:
    """Test MediaLink initialization."""

    def test_init_basic(self):
        """Create MediaLink with type and ID."""
        link = MediaLink('yt', 'dQw4w9WgXcQ')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_init_different_types(self):
        """Create MediaLink with various types."""
        link_yt = MediaLink('yt', 'video123')
        link_tw = MediaLink('tw', 'channel_name')
        link_dm = MediaLink('dm', 'dailymotion_id')

        assert link_yt.type == 'yt'
        assert link_tw.type == 'tw'
        assert link_dm.type == 'dm'

    def test_init_empty_id(self):
        """Create MediaLink with empty ID."""
        link = MediaLink('yt', '')
        assert link.type == 'yt'
        assert link.id == ''

    def test_init_special_characters_in_id(self):
        """Create MediaLink with special characters in ID."""
        link = MediaLink('sc', 'artist/song-name_123')
        assert link.id == 'artist/song-name_123'


class TestMediaLinkStringRepresentation:
    """Test MediaLink string representations and equality."""

    def test_str(self):
        """Test __str__ returns 'type:id' format."""
        link = MediaLink('yt', 'dQw4w9WgXcQ')
        assert str(link) == 'yt:dQw4w9WgXcQ'

    def test_str_different_types(self):
        """Test __str__ with various types."""
        assert str(MediaLink('tw', 'ninja')) == 'tw:ninja'
        assert str(MediaLink('dm', 'x123abc')) == 'dm:x123abc'

    def test_repr(self):
        """Test __repr__ returns constructor format."""
        link = MediaLink('vi', '123456')
        assert repr(link) == "MediaLink('vi', '123456')"

    def test_eq_same_link(self):
        """Test equality for identical links."""
        link1 = MediaLink('yt', 'video123')
        link2 = MediaLink('yt', 'video123')
        assert link1 == link2

    def test_eq_different_id(self):
        """Test inequality for different IDs."""
        link1 = MediaLink('yt', 'video123')
        link2 = MediaLink('yt', 'video456')
        assert link1 != link2

    def test_eq_different_type(self):
        """Test inequality for different types."""
        link1 = MediaLink('yt', 'video123')
        link2 = MediaLink('tw', 'video123')
        assert link1 != link2

    def test_eq_different_class(self):
        """Test inequality with non-MediaLink object."""
        link = MediaLink('yt', 'video123')
        assert link != "yt:video123"
        assert link != {'type': 'yt', 'id': 'video123'}


class TestMediaLinkUrl:
    """Test MediaLink.url property."""

    def test_url_youtube(self):
        """Get URL for YouTube video."""
        link = MediaLink('yt', 'dQw4w9WgXcQ')
        assert link.url == 'https://youtube.com/watch?v=dQw4w9WgXcQ'

    def test_url_youtube_playlist(self):
        """Get URL for YouTube playlist."""
        link = MediaLink('yp', 'PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf')
        assert link.url == 'https://youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf'

    def test_url_twitch_channel(self):
        """Get URL for Twitch channel."""
        link = MediaLink('tw', 'ninja')
        assert link.url == 'https://twitch.tv/ninja'

    def test_url_twitch_clip(self):
        """Get URL for Twitch clip."""
        link = MediaLink('tc', 'AwesomeClip')
        assert link.url == 'https://clips.twitch.tv/AwesomeClip'

    def test_url_vimeo(self):
        """Get URL for Vimeo video."""
        link = MediaLink('vi', '123456789')
        assert link.url == 'https://vimeo.com/123456789'

    def test_url_dailymotion(self):
        """Get URL for Dailymotion video."""
        link = MediaLink('dm', 'x7tgad0')
        assert link.url == 'https://dailymotion.com/video/x7tgad0'

    def test_url_soundcloud(self):
        """Get URL for SoundCloud track."""
        link = MediaLink('sc', 'artist/track-name')
        assert link.url == 'https://soundcloud.com/artist/track-name'

    def test_url_google_drive(self):
        """Get URL for Google Drive file."""
        link = MediaLink('gd', '1ABC-xyz_123')
        assert link.url == 'https://drive.google.com/file/d/1ABC-xyz_123'

    def test_url_imgur_album(self):
        """Get URL for Imgur album."""
        link = MediaLink('im', 'a1b2c3')
        assert link.url == 'https://imgur.com/a/a1b2c3'

    def test_url_streamable(self):
        """Get URL for Streamable video."""
        link = MediaLink('sb', 'abc123')
        assert link.url == 'https://streamable.com/abc123'

    def test_url_raw_file(self):
        """Get URL for raw file (fi type)."""
        link = MediaLink('fi', 'https://example.com/video.mp4')
        assert link.url == 'https://example.com/video.mp4'

    def test_url_m3u8_stream(self):
        """Get URL for M3U8 stream (hl type)."""
        link = MediaLink('hl', 'https://example.com/stream.m3u8')
        assert link.url == 'https://example.com/stream.m3u8'

    def test_url_rtmp_stream(self):
        """Get URL for RTMP stream (rt type)."""
        link = MediaLink('rt', 'rtmp://example.com/live/stream')
        assert link.url == 'rtmp://example.com/live/stream'

    def test_url_custom_type(self):
        """Get URL for custom type (cm type)."""
        link = MediaLink('cm', 'https://example.com/custom.json')
        assert link.url == 'https://example.com/custom.json'

    def test_url_unknown_type_logs_warning(self):
        """Test unknown type logs warning and returns type:id format."""
        link = MediaLink('unknown', 'some_id')
        with patch.object(MediaLink.logger, 'warning') as mock_warn:
            url = link.url
            assert url == 'unknown:some_id'
            mock_warn.assert_called_once()


class TestFromUrlYoutube:
    """Test YouTube URL parsing."""

    def test_youtube_watch_url(self):
        """Parse standard YouTube watch URL."""
        link = MediaLink.from_url('https://youtube.com/watch?v=dQw4w9WgXcQ')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_youtube_short_url(self):
        """Parse short youtu.be URL."""
        link = MediaLink.from_url('https://youtu.be/dQw4w9WgXcQ')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_youtube_with_timestamp(self):
        """Parse YouTube URL with timestamp."""
        link = MediaLink.from_url('https://youtube.com/watch?v=dQw4w9WgXcQ&t=42s')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_youtube_playlist(self):
        """Parse YouTube playlist URL."""
        link = MediaLink.from_url('https://youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf')
        assert link.type == 'yp'
        assert link.id == 'PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf'

    def test_youtube_embedded_player_feature_removed(self):
        """Test feature=player_embedded is removed from URL."""
        link = MediaLink.from_url('https://youtube.com/watch?feature=player_embedded&v=dQw4w9WgXcQ')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'


class TestFromUrlTwitch:
    """Test Twitch URL parsing."""

    def test_twitch_clip(self):
        """Parse Twitch clip URL."""
        link = MediaLink.from_url('https://clips.twitch.tv/AwesomeClipName')
        assert link.type == 'tc'
        assert link.id == 'AwesomeClipName'

    def test_twitch_video(self):
        """Parse Twitch video URL."""
        link = MediaLink.from_url('https://twitch.tv/videos/123456789')
        assert link.type == 'tv'
        assert link.id == 'v123456789'

    def test_twitch_channel(self):
        """Parse Twitch channel URL."""
        link = MediaLink.from_url('https://twitch.tv/ninja')
        assert link.type == 'tw'
        assert link.id == 'ninja'

    def test_twitch_channel_with_dashes(self):
        """Parse Twitch channel with dashes in name."""
        link = MediaLink.from_url('https://twitch.tv/channel-name_123')
        assert link.type == 'tw'
        assert link.id == 'channel-name_123'


class TestFromUrlOtherProviders:
    """Test other media provider URL parsing."""

    def test_vimeo(self):
        """Parse Vimeo URL."""
        link = MediaLink.from_url('https://vimeo.com/123456789')
        assert link.type == 'vi'
        assert link.id == '123456789'

    def test_dailymotion(self):
        """Parse Dailymotion URL."""
        link = MediaLink.from_url('https://dailymotion.com/video/x7tgad0')
        assert link.type == 'dm'
        assert link.id == 'x7tgad0'

    def test_soundcloud(self):
        """Parse SoundCloud URL."""
        url = 'https://soundcloud.com/artist-name/track-name'
        link = MediaLink.from_url(url)
        assert link.type == 'sc'
        assert link.id == url

    def test_google_drive_file(self):
        """Parse Google Drive file URL."""
        link = MediaLink.from_url('https://drive.google.com/file/d/1ABC-xyz_123/view')
        assert link.type == 'gd'
        assert link.id == '1ABC-xyz_123'

    def test_google_docs_file(self):
        """Parse Google Docs file URL."""
        link = MediaLink.from_url('https://docs.google.com/file/d/1ABC-xyz_123')
        assert link.type == 'gd'
        assert link.id == '1ABC-xyz_123'

    def test_google_drive_open(self):
        """Parse Google Drive open?id= URL."""
        link = MediaLink.from_url('https://drive.google.com/open?id=1ABC-xyz_123')
        assert link.type == 'gd'
        assert link.id == '1ABC-xyz_123'

    def test_imgur_album(self):
        """Parse Imgur album URL."""
        link = MediaLink.from_url('https://imgur.com/a/abc123')
        assert link.type == 'im'
        assert link.id == 'abc123'

    def test_streamable(self):
        """Parse Streamable URL."""
        link = MediaLink.from_url('https://streamable.com/xyz789')
        assert link.type == 'sb'
        assert link.id == 'xyz789'

    def test_vidme(self):
        """Parse Vid.me URL."""
        link = MediaLink.from_url('https://vid.me/abc123')
        assert link.type == 'vm'
        assert link.id == 'abc123'

    def test_vidme_embedded(self):
        """Parse Vid.me embedded URL."""
        link = MediaLink.from_url('https://vid.me/embedded/xyz456')
        assert link.type == 'vm'
        assert link.id == 'xyz456'

    def test_livestream(self):
        """Parse Livestream URL."""
        link = MediaLink.from_url('https://livestream.com/event-name')
        assert link.type == 'li'
        assert link.id == 'event-name'

    def test_ustream(self):
        """Parse Ustream URL."""
        link = MediaLink.from_url('https://ustream.tv/channel-name')
        assert link.type == 'us'
        assert link.id == 'channel-name'

    def test_hitbox(self):
        """Parse Hitbox URL."""
        link = MediaLink.from_url('https://hitbox.tv/streamer')
        assert link.type == 'hb'
        assert link.id == 'streamer'

    def test_smashcast(self):
        """Parse Smashcast URL (Hitbox rebrand)."""
        link = MediaLink.from_url('https://smashcast.tv/streamer')
        assert link.type == 'hb'
        assert link.id == 'streamer'


class TestFromUrlRawFiles:
    """Test raw file URL parsing."""

    def test_https_mp4(self):
        """Parse HTTPS MP4 file."""
        link = MediaLink.from_url('https://example.com/video.mp4')
        assert link.type == 'fi'
        assert link.id == 'https://example.com/video.mp4'

    def test_https_webm(self):
        """Parse HTTPS WebM file."""
        link = MediaLink.from_url('https://example.com/video.webm')
        assert link.type == 'fi'
        assert link.id == 'https://example.com/video.webm'

    def test_https_ogg(self):
        """Parse HTTPS OGG file."""
        link = MediaLink.from_url('https://example.com/video.ogg')
        assert link.type == 'fi'
        assert link.id == 'https://example.com/video.ogg'

    def test_https_mp3(self):
        """Parse HTTPS MP3 file."""
        link = MediaLink.from_url('https://example.com/audio.mp3')
        assert link.type == 'fi'
        assert link.id == 'https://example.com/audio.mp3'

    def test_https_flv(self):
        """Parse HTTPS FLV file."""
        link = MediaLink.from_url('https://example.com/video.flv')
        assert link.type == 'fi'
        assert link.id == 'https://example.com/video.flv'

    def test_https_m3u8_stream(self):
        """Parse HTTPS M3U8 stream (matches before file extension check)."""
        link = MediaLink.from_url('https://example.com/stream.m3u8')
        assert link.type == 'hl'
        assert link.id == 'https://example.com/stream.m3u8'

    def test_https_json_custom_embed(self):
        """Parse HTTPS JSON file as custom embed."""
        link = MediaLink.from_url('https://example.com/player.json')
        assert link.type == 'cm'
        assert link.id == 'https://example.com/player.json'

    def test_http_file_rejected(self):
        """Test HTTP (not HTTPS) file is rejected."""
        with pytest.raises(ValueError, match='must begin with "https"'):
            MediaLink.from_url('http://example.com/video.mp4')

    def test_https_unsupported_extension_rejected(self):
        """Test HTTPS file with unsupported extension is rejected."""
        with pytest.raises(ValueError, match='does not match the supported file extensions'):
            MediaLink.from_url('https://example.com/video.avi')

    def test_https_no_extension_rejected(self):
        """Test HTTPS URL with no extension is rejected."""
        with pytest.raises(ValueError, match='does not match the supported file extensions'):
            MediaLink.from_url('https://example.com/video')


class TestFromUrlCustomTypes:
    """Test custom type prefix parsing."""

    def test_dm_prefix(self):
        """Parse dm: prefix for Dailymotion."""
        link = MediaLink.from_url('dm:x7tgad0')
        assert link.type == 'dm'
        assert link.id == 'x7tgad0'

    def test_fi_prefix(self):
        """Parse fi: prefix for raw file."""
        link = MediaLink.from_url('fi:https://example.com/video.mp4')
        assert link.type == 'fi'
        assert link.id == 'https://example.com/video.mp4'

    def test_cm_prefix(self):
        """Parse cm: prefix for custom embed."""
        link = MediaLink.from_url('cm:https://example.com/custom.json')
        assert link.type == 'cm'
        assert link.id == 'https://example.com/custom.json'

    def test_generic_prefix(self):
        """Parse generic XX: prefix for custom types."""
        link = MediaLink.from_url('rt:rtmp://example.com/stream')
        assert link.type == 'rt'
        assert link.id == 'rtmp://example.com/stream'


class TestFromUrlEdgeCases:
    """Test edge cases and special scenarios."""

    def test_rtmp_scheme(self):
        """Parse RTMP URL."""
        link = MediaLink.from_url('rtmp://example.com/live/stream')
        assert link.type == 'rt'
        assert link.id == 'rtmp://example.com/live/stream'

    def test_url_with_leading_trailing_whitespace(self):
        """Parse URL with whitespace (stripped)."""
        link = MediaLink.from_url('  https://youtube.com/watch?v=dQw4w9WgXcQ  ')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_url_with_query_parameters(self):
        """Parse URL with multiple query parameters."""
        link = MediaLink.from_url('https://youtube.com/watch?v=dQw4w9WgXcQ&feature=share&t=10s')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_url_with_fragment(self):
        """Parse URL with fragment."""
        link = MediaLink.from_url('https://youtube.com/watch?v=dQw4w9WgXcQ#t=10s')
        assert link.type == 'yt'
        assert link.id == 'dQw4w9WgXcQ'

    def test_http_unknown_url_rejected(self):
        """Test HTTP URL with unknown domain is rejected."""
        with pytest.raises(ValueError, match='must begin with "https"'):
            MediaLink.from_url('http://unknown-site.com/video')

    def test_file_types_list(self):
        """Test FILE_TYPES class attribute exists."""
        assert hasattr(MediaLink, 'FILE_TYPES')
        assert isinstance(MediaLink.FILE_TYPES, list)
        assert '.mp4' in MediaLink.FILE_TYPES
        assert '.webm' in MediaLink.FILE_TYPES

    def test_url_to_link_patterns(self):
        """Test URL_TO_LINK class attribute exists."""
        assert hasattr(MediaLink, 'URL_TO_LINK')
        assert isinstance(MediaLink.URL_TO_LINK, list)
        assert len(MediaLink.URL_TO_LINK) > 20  # Many patterns

    def test_link_to_url_mapping(self):
        """Test LINK_TO_URL class attribute exists."""
        assert hasattr(MediaLink, 'LINK_TO_URL')
        assert isinstance(MediaLink.LINK_TO_URL, dict)
        assert 'yt' in MediaLink.LINK_TO_URL
        assert 'tw' in MediaLink.LINK_TO_URL


class TestRoundTrip:
    """Test URL -> MediaLink -> URL round-trip conversions."""

    def test_youtube_roundtrip(self):
        """Test YouTube URL round-trip."""
        original = 'https://youtube.com/watch?v=dQw4w9WgXcQ'
        link = MediaLink.from_url(original)
        assert link.url == original

    def test_twitch_channel_roundtrip(self):
        """Test Twitch channel URL round-trip."""
        original = 'https://twitch.tv/ninja'
        link = MediaLink.from_url(original)
        assert link.url == original

    def test_vimeo_roundtrip(self):
        """Test Vimeo URL round-trip."""
        original = 'https://vimeo.com/123456789'
        link = MediaLink.from_url(original)
        assert link.url == original

    def test_raw_file_roundtrip(self):
        """Test raw file URL round-trip."""
        original = 'https://example.com/video.mp4'
        link = MediaLink.from_url(original)
        assert link.url == original
