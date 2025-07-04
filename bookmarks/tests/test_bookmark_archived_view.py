import urllib.parse

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from bookmarks.models import BookmarkSearch, UserProfile
from bookmarks.tests.helpers import (
    BookmarkFactoryMixin,
    BookmarkListTestMixin,
    TagCloudTestMixin,
)


class BookmarkArchivedViewTestCase(
    TestCase, BookmarkFactoryMixin, BookmarkListTestMixin, TagCloudTestMixin
):

    def setUp(self) -> None:
        user = self.get_or_create_test_user()
        self.client.force_login(user)

    def assertEditLink(self, response, url):
        html = response.content.decode()
        self.assertInHTML(
            f"""
            <a href="{url}">Edit</a>        
        """,
            html,
        )

    def assertBulkActionForm(self, response, url: str):
        soup = self.make_soup(response.content.decode())
        form = soup.select_one("form.bookmark-actions")
        self.assertIsNotNone(form)
        self.assertEqual(form.attrs["action"], url)

    def test_should_list_archived_and_user_owned_bookmarks(self):
        other_user = User.objects.create_user(
            "otheruser", "otheruser@example.com", "password123"
        )
        visible_bookmarks = self.setup_numbered_bookmarks(3, archived=True)
        invisible_bookmarks = [
            self.setup_bookmark(is_archived=False),
            self.setup_bookmark(is_archived=True, user=other_user),
        ]

        response = self.client.get(reverse("linkding:bookmarks.archived"))

        self.assertVisibleBookmarks(response, visible_bookmarks)
        self.assertInvisibleBookmarks(response, invisible_bookmarks)

    def test_should_list_bookmarks_matching_query(self):
        visible_bookmarks = self.setup_numbered_bookmarks(
            3, prefix="foo", archived=True
        )
        invisible_bookmarks = self.setup_numbered_bookmarks(
            3, prefix="bar", archived=True
        )

        response = self.client.get(reverse("linkding:bookmarks.archived") + "?q=foo")

        self.assertVisibleBookmarks(response, visible_bookmarks)
        self.assertInvisibleBookmarks(response, invisible_bookmarks)

    def test_should_list_bookmarks_matching_bundle(self):
        visible_bookmarks = self.setup_numbered_bookmarks(
            3, prefix="foo", archived=True
        )
        invisible_bookmarks = self.setup_numbered_bookmarks(
            3, prefix="bar", archived=True
        )

        bundle = self.setup_bundle(search="foo")

        response = self.client.get(
            reverse("linkding:bookmarks.archived") + f"?bundle={bundle.id}"
        )

        self.assertVisibleBookmarks(response, visible_bookmarks)
        self.assertInvisibleBookmarks(response, invisible_bookmarks)

    def test_should_list_tags_for_archived_and_user_owned_bookmarks(self):
        other_user = User.objects.create_user(
            "otheruser", "otheruser@example.com", "password123"
        )
        visible_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=True
        )
        unarchived_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=False, tag_prefix="unarchived"
        )
        other_user_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=True, user=other_user, tag_prefix="otheruser"
        )

        visible_tags = self.get_tags_from_bookmarks(visible_bookmarks)
        invisible_tags = self.get_tags_from_bookmarks(
            unarchived_bookmarks + other_user_bookmarks
        )

        response = self.client.get(reverse("linkding:bookmarks.archived"))

        self.assertVisibleTags(response, visible_tags)
        self.assertInvisibleTags(response, invisible_tags)

    def test_should_list_tags_for_bookmarks_matching_query(self):
        visible_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=True, prefix="foo", tag_prefix="foo"
        )
        invisible_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=True, prefix="bar", tag_prefix="bar"
        )

        visible_tags = self.get_tags_from_bookmarks(visible_bookmarks)
        invisible_tags = self.get_tags_from_bookmarks(invisible_bookmarks)

        response = self.client.get(reverse("linkding:bookmarks.archived") + "?q=foo")

        self.assertVisibleTags(response, visible_tags)
        self.assertInvisibleTags(response, invisible_tags)

    def test_should_list_tags_for_bookmarks_matching_bundle(self):
        visible_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=True, prefix="foo", tag_prefix="foo"
        )
        invisible_bookmarks = self.setup_numbered_bookmarks(
            3, with_tags=True, archived=True, prefix="bar", tag_prefix="bar"
        )

        visible_tags = self.get_tags_from_bookmarks(visible_bookmarks)
        invisible_tags = self.get_tags_from_bookmarks(invisible_bookmarks)

        bundle = self.setup_bundle(search="foo")

        response = self.client.get(
            reverse("linkding:bookmarks.archived") + f"?bundle={bundle.id}"
        )

        self.assertVisibleTags(response, visible_tags)
        self.assertInvisibleTags(response, invisible_tags)

    def test_should_list_bookmarks_and_tags_for_search_preferences(self):
        user_profile = self.user.profile
        user_profile.search_preferences = {
            "unread": BookmarkSearch.FILTER_UNREAD_YES,
        }
        user_profile.save()

        unread_bookmarks = self.setup_numbered_bookmarks(
            3,
            archived=True,
            unread=True,
            with_tags=True,
            prefix="unread",
            tag_prefix="unread",
        )
        read_bookmarks = self.setup_numbered_bookmarks(
            3,
            archived=True,
            unread=False,
            with_tags=True,
            prefix="read",
            tag_prefix="read",
        )

        unread_tags = self.get_tags_from_bookmarks(unread_bookmarks)
        read_tags = self.get_tags_from_bookmarks(read_bookmarks)

        response = self.client.get(reverse("linkding:bookmarks.archived"))
        self.assertVisibleBookmarks(response, unread_bookmarks)
        self.assertInvisibleBookmarks(response, read_bookmarks)
        self.assertVisibleTags(response, unread_tags)
        self.assertInvisibleTags(response, read_tags)

    def test_should_display_selected_tags_from_query(self):
        tags = [
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
        ]
        self.setup_bookmark(is_archived=True, tags=tags)

        response = self.client.get(
            reverse("linkding:bookmarks.archived")
            + f"?q=%23{tags[0].name}+%23{tags[1].name}"
        )

        self.assertSelectedTags(response, [tags[0], tags[1]])

    def test_should_not_display_search_terms_from_query_as_selected_tags_in_strict_mode(
        self,
    ):
        tags = [
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
        ]
        self.setup_bookmark(title=tags[0].name, tags=tags, is_archived=True)

        response = self.client.get(
            reverse("linkding:bookmarks.archived")
            + f"?q={tags[0].name}+%23{tags[1].name.upper()}"
        )

        self.assertSelectedTags(response, [tags[1]])

    def test_should_display_search_terms_from_query_as_selected_tags_in_lax_mode(self):
        self.user.profile.tag_search = UserProfile.TAG_SEARCH_LAX
        self.user.profile.save()

        tags = [
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
            self.setup_tag(),
        ]
        self.setup_bookmark(tags=tags, is_archived=True)

        response = self.client.get(
            reverse("linkding:bookmarks.archived")
            + f"?q={tags[0].name}+%23{tags[1].name.upper()}"
        )

        self.assertSelectedTags(response, [tags[0], tags[1]])

    def test_should_open_bookmarks_in_new_page_by_default(self):
        visible_bookmarks = self.setup_numbered_bookmarks(3, archived=True)

        response = self.client.get(reverse("linkding:bookmarks.archived"))

        self.assertVisibleBookmarks(response, visible_bookmarks, "_blank")

    def test_should_open_bookmarks_in_same_page_if_specified_in_user_profile(self):
        user = self.get_or_create_test_user()
        user.profile.bookmark_link_target = UserProfile.BOOKMARK_LINK_TARGET_SELF
        user.profile.save()

        visible_bookmarks = self.setup_numbered_bookmarks(3, archived=True)

        response = self.client.get(reverse("linkding:bookmarks.archived"))

        self.assertVisibleBookmarks(response, visible_bookmarks, "_self")

    def test_edit_link_return_url_respects_search_options(self):
        bookmark = self.setup_bookmark(title="foo", is_archived=True)
        edit_url = reverse("linkding:bookmarks.edit", args=[bookmark.id])
        base_url = reverse("linkding:bookmarks.archived")

        # without query params
        return_url = urllib.parse.quote(base_url)
        url = f"{edit_url}?return_url={return_url}"

        response = self.client.get(base_url)
        self.assertEditLink(response, url)

        # with query
        url_params = "?q=foo"
        return_url = urllib.parse.quote(base_url + url_params)
        url = f"{edit_url}?return_url={return_url}"

        response = self.client.get(base_url + url_params)
        self.assertEditLink(response, url)

        # with query and sort and page
        url_params = "?q=foo&sort=title_asc&page=2"
        return_url = urllib.parse.quote(base_url + url_params)
        url = f"{edit_url}?return_url={return_url}"

        response = self.client.get(base_url + url_params)
        self.assertEditLink(response, url)

    def test_bulk_edit_respects_search_options(self):
        action_url = reverse("linkding:bookmarks.archived.action")
        base_url = reverse("linkding:bookmarks.archived")

        # without params
        url = f"{action_url}"

        response = self.client.get(base_url)
        self.assertBulkActionForm(response, url)

        # with query
        url_params = "?q=foo"
        url = f"{action_url}?q=foo"

        response = self.client.get(base_url + url_params)
        self.assertBulkActionForm(response, url)

        # with query and sort
        url_params = "?q=foo&sort=title_asc"
        url = f"{action_url}?q=foo&sort=title_asc"

        response = self.client.get(base_url + url_params)
        self.assertBulkActionForm(response, url)

    def test_allowed_bulk_actions(self):
        url = reverse("linkding:bookmarks.archived")
        response = self.client.get(url)
        html = response.content.decode()

        self.assertInHTML(
            f"""
          <select name="bulk_action" class="form-select select-sm">
            <option value="bulk_unarchive">Unarchive</option>
            <option value="bulk_delete">Delete</option>
            <option value="bulk_tag">Add tags</option>
            <option value="bulk_untag">Remove tags</option>
            <option value="bulk_read">Mark as read</option>
            <option value="bulk_unread">Mark as unread</option>
            <option value="bulk_refresh">Refresh from website</option>
          </select>
        """,
            html,
        )

    def test_allowed_bulk_actions_with_sharing_enabled(self):
        user_profile = self.user.profile
        user_profile.enable_sharing = True
        user_profile.save()

        url = reverse("linkding:bookmarks.archived")
        response = self.client.get(url)
        html = response.content.decode()

        self.assertInHTML(
            f"""
          <select name="bulk_action" class="form-select select-sm">
            <option value="bulk_unarchive">Unarchive</option>
            <option value="bulk_delete">Delete</option>
            <option value="bulk_tag">Add tags</option>
            <option value="bulk_untag">Remove tags</option>
            <option value="bulk_read">Mark as read</option>
            <option value="bulk_unread">Mark as unread</option>
            <option value="bulk_share">Share</option>
            <option value="bulk_unshare">Unshare</option>
            <option value="bulk_refresh">Refresh from website</option>
          </select>
        """,
            html,
        )

    def test_apply_search_preferences(self):
        # no params
        response = self.client.post(reverse("linkding:bookmarks.archived"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("linkding:bookmarks.archived"))

        # some params
        response = self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "q": "foo",
                "sort": BookmarkSearch.SORT_TITLE_ASC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("linkding:bookmarks.archived") + "?q=foo&sort=title_asc",
        )

        # params with default value are removed
        response = self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "q": "foo",
                "user": "",
                "sort": BookmarkSearch.SORT_ADDED_DESC,
                "shared": BookmarkSearch.FILTER_SHARED_OFF,
                "unread": BookmarkSearch.FILTER_UNREAD_YES,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("linkding:bookmarks.archived") + "?q=foo&unread=yes"
        )

        # page is removed
        response = self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "q": "foo",
                "page": "2",
                "sort": BookmarkSearch.SORT_TITLE_ASC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("linkding:bookmarks.archived") + "?q=foo&sort=title_asc",
        )

    def test_save_search_preferences(self):
        user_profile = self.user.profile

        # no params
        self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "save": "",
            },
        )
        user_profile.refresh_from_db()
        self.assertEqual(
            user_profile.search_preferences,
            {
                "sort": BookmarkSearch.SORT_ADDED_DESC,
                "shared": BookmarkSearch.FILTER_SHARED_OFF,
                "unread": BookmarkSearch.FILTER_UNREAD_OFF,
            },
        )

        # with param
        self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "save": "",
                "sort": BookmarkSearch.SORT_TITLE_ASC,
            },
        )
        user_profile.refresh_from_db()
        self.assertEqual(
            user_profile.search_preferences,
            {
                "sort": BookmarkSearch.SORT_TITLE_ASC,
                "shared": BookmarkSearch.FILTER_SHARED_OFF,
                "unread": BookmarkSearch.FILTER_UNREAD_OFF,
            },
        )

        # add a param
        self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "save": "",
                "sort": BookmarkSearch.SORT_TITLE_ASC,
                "unread": BookmarkSearch.FILTER_UNREAD_YES,
            },
        )
        user_profile.refresh_from_db()
        self.assertEqual(
            user_profile.search_preferences,
            {
                "sort": BookmarkSearch.SORT_TITLE_ASC,
                "shared": BookmarkSearch.FILTER_SHARED_OFF,
                "unread": BookmarkSearch.FILTER_UNREAD_YES,
            },
        )

        # remove a param
        self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "save": "",
                "unread": BookmarkSearch.FILTER_UNREAD_YES,
            },
        )
        user_profile.refresh_from_db()
        self.assertEqual(
            user_profile.search_preferences,
            {
                "sort": BookmarkSearch.SORT_ADDED_DESC,
                "shared": BookmarkSearch.FILTER_SHARED_OFF,
                "unread": BookmarkSearch.FILTER_UNREAD_YES,
            },
        )

        # ignores non-preferences
        self.client.post(
            reverse("linkding:bookmarks.archived"),
            {
                "save": "",
                "q": "foo",
                "user": "john",
                "page": "3",
                "sort": BookmarkSearch.SORT_TITLE_ASC,
            },
        )
        user_profile.refresh_from_db()
        self.assertEqual(
            user_profile.search_preferences,
            {
                "sort": BookmarkSearch.SORT_TITLE_ASC,
                "shared": BookmarkSearch.FILTER_SHARED_OFF,
                "unread": BookmarkSearch.FILTER_UNREAD_OFF,
            },
        )

    def test_url_encode_bookmark_actions_url(self):
        url = reverse("linkding:bookmarks.archived") + "?q=%23foo"
        response = self.client.get(url)
        html = response.content.decode()
        soup = self.make_soup(html)
        actions_form = soup.select("form.bookmark-actions")[0]

        self.assertEqual(
            actions_form.attrs["action"],
            "/bookmarks/archived/action?q=%23foo",
        )

    def test_encode_search_params(self):
        bookmark = self.setup_bookmark(description="alert('xss')", is_archived=True)

        url = reverse("linkding:bookmarks.archived") + "?q=alert(%27xss%27)"
        response = self.client.get(url)
        self.assertNotContains(response, "alert('xss')")
        self.assertContains(response, bookmark.url)

        url = reverse("linkding:bookmarks.archived") + "?sort=alert(%27xss%27)"
        response = self.client.get(url)
        self.assertNotContains(response, "alert('xss')")

        url = reverse("linkding:bookmarks.archived") + "?unread=alert(%27xss%27)"
        response = self.client.get(url)
        self.assertNotContains(response, "alert('xss')")

        url = reverse("linkding:bookmarks.archived") + "?shared=alert(%27xss%27)"
        response = self.client.get(url)
        self.assertNotContains(response, "alert('xss')")

        url = reverse("linkding:bookmarks.archived") + "?user=alert(%27xss%27)"
        response = self.client.get(url)
        self.assertNotContains(response, "alert('xss')")

        url = reverse("linkding:bookmarks.archived") + "?page=alert(%27xss%27)"
        response = self.client.get(url)
        self.assertNotContains(response, "alert('xss')")

    def test_turbo_frame_details_modal_renders_details_modal_update(self):
        bookmark = self.setup_bookmark()
        url = reverse("linkding:bookmarks.archived") + f"?bookmark_id={bookmark.id}"
        response = self.client.get(url, headers={"Turbo-Frame": "details-modal"})

        self.assertEqual(200, response.status_code)

        soup = self.make_soup(response.content.decode())
        self.assertIsNotNone(soup.select_one("turbo-frame#details-modal"))
        self.assertIsNone(soup.select_one("#bookmark-list-container"))
        self.assertIsNone(soup.select_one("#tag-cloud-container"))

    def test_does_not_include_rss_feed(self):
        response = self.client.get(reverse("linkding:bookmarks.archived"))
        soup = self.make_soup(response.content.decode())

        feed = soup.select_one('head link[type="application/rss+xml"]')
        self.assertIsNone(feed)

    def test_hide_bundles_when_enabled_in_profile(self):
        # visible by default
        response = self.client.get(reverse("linkding:bookmarks.archived"))
        html = response.content.decode()

        self.assertInHTML('<h2 id="bundles-heading">Bundles</h2>', html)

        # hidden when disabled in profile
        user_profile = self.get_or_create_test_user().profile
        user_profile.hide_bundles = True
        user_profile.save()

        response = self.client.get(reverse("linkding:bookmarks.archived"))
        html = response.content.decode()

        self.assertInHTML('<h2 id="bundles-heading">Bundles</h2>', html, count=0)
