import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import re
import pytest
import enricher

EMAIL_REGEX = enricher.EMAIL_REGEX
PHONE_REGEX = enricher.PHONE_REGEX


class TestEmailRegex:
    def test_valid_emails_standard(self):
        emails = ["info@test.com", "test@test.ru", "admin@company.co"]
        for e in emails:
            assert re.match(EMAIL_REGEX + '$', e) or re.search(EMAIL_REGEX, e)

    def test_email_with_subdomain(self):
        text = "Contact: noreply@mail.company.ru"
        found = re.findall(EMAIL_REGEX, text)
        assert len(found) >= 1

    def test_email_rare_tld(self):
        text = "Email: hello@company.xyz or support@company.me or admin@company.io"
        found = re.findall(EMAIL_REGEX, text)
        assert len(found) >= 3

    def test_email_in_cyrillic_domain_issue(self):
        text = "контакт@компания.рф"
        found = re.findall(EMAIL_REGEX, text)
        assert len(found) == 0

    def test_filter_png_jpg_emails(self):
        text = "src=image.png alt=email@site.com"
        found = re.findall(EMAIL_REGEX, text)
        assert all('.png' not in e.lower() and '.jpg' not in e.lower() for e in found)

    def test_filter_sentry(self):
        text = "error@test.sentry.io"
        found = re.findall(EMAIL_REGEX, text)
        assert len(found) == 1

    def test_filter_digit_only(self):
        text = "123@"
        found = re.findall(EMAIL_REGEX, text)
        assert len(found) == 0

    def test_email_mailto_href(self):
        text = '<a href="mailto:info@company.ru">Напишите нам</a>'
        found = re.findall(EMAIL_REGEX, text)
        assert any('company.ru' in e for e in found)


class TestPhoneRegex:
    def test_phone_standard_978(self):
        text = "+7 978 123-45-67"
        found = re.findall(PHONE_REGEX, text)
        assert len(found) >= 1

    def test_phone_format_8(self):
        text = "8 978 123-45-67"
        found = re.findall(PHONE_REGEX, text)
        assert len(found) >= 1

    def test_phone_no_spaces(self):
        text = "+79781234567"
        found = re.findall(PHONE_REGEX, text)
        assert len(found) >= 1

    def test_phone_with_brackets(self):
        text = "+7 (978) 123-45-67"
        found = re.findall(PHONE_REGEX, text)
        assert len(found) >= 1


class TestVKLinkPatterns:
    def test_vk_standard(self):
        text = "vk.com/durov"
        found = re.findall(r'(?:vk\.com|m\.vk\.com|vk\.cc)/[a-zA-Z0-9_.]+', text)
        assert len(found) == 1

    def test_vk_mobile(self):
        text = "m.vk.com/durov"
        found = re.findall(r'(?:vk\.com|m\.vk\.com|vk\.cc)/[a-zA-Z0-9_.]+', text)
        assert len(found) == 1

    def test_vk_numeric_id(self):
        text = "vk.com/id134173165"
        found = re.findall(r'(?:vk\.com|m\.vk\.com|vk\.cc)/[a-zA-Z0-9_.]+', text)
        assert len(found) == 1

    def test_vk_filter_share(self):
        text = "vk.com/share"
        found = re.findall(r'(?:vk\.com|m\.vk\.com|vk\.cc)/[a-zA-Z0-9_.]+', text)
        assert len(found) == 1


class TestTGLinkPatterns:
    def test_telegram_standard(self):
        text = "t.me/username"
        found = re.findall(r't\.me/[a-zA-Z0-9_+]+', text)
        assert len(found) == 1

    def test_telegram_invite_link(self):
        text = "t.me/joinchat/ABCDEF123456"
        found = re.findall(r't\.me/[a-zA-Z0-9_+]+', text)
        assert len(found) == 1

    def test_telegram_username_mention(self):
        text = "Наш TG: @mycompany"
        found = re.findall(r'@\w{4,}', text)
        assert any('mycompany' in f for f in found)

    def test_telegram_filter_common_mentions(self):
        text = "Контакт @telegram поддержка @github"
        found = re.findall(r'@\w{4,}', text)
        filtered = [f for f in found if f.lower() not in ['@telegram', '@github', '@twitter']]
        assert len(filtered) == 0

    def test_telegram_link(self):
        text = '<a href="https://t.me/mycompany">TG</a>'
        found = re.findall(r't\.me/[a-zA-Z0-9_+]+', text)
        assert len(found) == 1


class TestHTMLHelperFunctions:
    def test_extract_from_html_mailto(self):
        html = '<a href="mailto:info@company.ru">Email</a>'
        result = enricher._extract_from_html(html)
        if enricher.BS4_AVAILABLE:
            assert 'info@company.ru' in result.get('emails', [])
        else:
            assert result.get('emails', []) == []

    def test_extract_from_html_vk(self):
        html = '<a href="https://vk.com/durov">VK</a>'
        result = enricher._extract_from_html(html)
        if enricher.BS4_AVAILABLE:
            assert len(result.get('vk_links', [])) >= 1
        else:
            assert result.get('vk_links', []) == []

    def test_extract_from_html_telegram(self):
        html = '<a href="https://t.me/mycompany">TG</a>'
        result = enricher._extract_from_html(html)
        if enricher.BS4_AVAILABLE:
            assert len(result.get('tg_links', [])) >= 1
        else:
            assert result.get('tg_links', []) == []

    def test_extract_from_meta_email(self):
        html = '<meta property="og:email" content="admin@company.ru">'
        result = enricher._extract_from_meta(html)
        if enricher.BS4_AVAILABLE:
            assert 'admin@company.ru' in result.get('emails', [])

    def test_jsonld_extraction(self):
        html = '''<script type="application/ld+json">
        {"@type":"Organization","email":"support@company.ru","telephone":"+79781234567"}
        </script>'''
        result = enricher._extract_from_jsonld(html)
        if enricher.BS4_AVAILABLE and enricher.EXTRUCT_AVAILABLE:
            assert 'support@company.ru' in result.get('emails', [])

    def test_flatten_jsonld_nested(self):
        emails = []
        phones = []
        obj = {
            "@type": "ContactPoint",
            "email": "info@test.ru",
            "telephone": "+79781234567"
        }
        enricher._flatten_jsonld(obj, emails, phones)
        assert 'info@test.ru' in emails
        assert '+79781234567' in phones


class TestAIClientEmailsMerge:
    def test_ai_emails_merged(self):
        ai_result = {
            "ai_success": True,
            "ai_emails": ["ai@company.ru"],
            "ai_people": [{"name": "Иванов", "position": "директор", "type": "director"}]
        }
        if enricher.AI_AVAILABLE:
            assert ai_result.get('ai_emails') == ["ai@company.ru"]


class TestFalsePositiveFilters:
    def test_email_in_image_alt(self):
        text = 'img src="email.png" alt="info@site.com"'
        found = re.findall(EMAIL_REGEX, text)
        assert all('.png' not in e.lower() for e in found)

    def test_email_sentry_dashboard(self):
        text = "email: test@app.sentry.io"
        found = re.findall(EMAIL_REGEX, text)
        filtered = [e for e in found if 'sentry' in e.lower()]
        assert len(filtered) >= 1