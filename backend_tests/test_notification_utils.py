from unittest.mock import AsyncMock, patch

from django.test import TestCase

from apis.chatroom_dispatcher.chatroom_dispatcher_model import ChatroomDispatchConfig
from apis.company.company_model import Company
from apis.connectors.connectors_model import Connectors, Tenant
from apis.conversation.conversation_models import Conversation
from apis.lookup.lookup_models import ConversationStage
from apis.message.message_models import Message
from apis.notification.notification_model import Notification
from apis.notification.notification_utils import (
    create_chatroom_notifications_payload,
    create_new_message_notifications_payload,
)
from apis.settings.settings_model import NewMessageNotificationSettings
from apis.user.user_model import User


class NotificationBusinessLogicTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Django isolates these shared fixtures so changes in one test do not affect another.
        cls.company = Company.objects.create(company_name="Notifications QA", company_mobile="10001")
        other_company = Company.objects.create(company_name="Other QA", company_mobile="10002")
        # Separate agent and owner records let us verify which assignment receives the alert.
        # English keeps the expected notification titles consistent.
        cls.agent = User.objects.create(company=cls.company, name="Agent", mobile_number="101", lang="en")
        cls.owner = User.objects.create(company=cls.company, name="Owner", mobile_number="102", lang="en")
        # These users must be excluded from fallback and mention notifications.
        cls.inactive = User.objects.create(company=cls.company, name="Inactive", mobile_number="103", is_active=False)
        cls.outsider = User.objects.create(company=other_company, name="Outsider", mobile_number="104")
        # The connector identifies the conversation's company and requires a tenant.
        tenant = Tenant.objects.create(company=cls.company, name="QA")
        connector = Connectors.objects.create(company=cls.company, tenant=tenant, connector_name="QA", connector_type="whatsapp")
        cls.stage = ConversationStage.objects.create(name="Notification QA")
        cls.conversation = Conversation.objects.create(
            name="Customer", number="20001", default_connector=connector,
            stage=cls.stage, agent=cls.agent, contact_owner=cls.owner,
        )
        cls.conversation.connectors.add(connector)
        # New-message notifications require settings that include the conversation's stage.
        cls.preferences = NewMessageNotificationSettings.objects.create(
            company=cls.company, enabled=True,
            recipient=NewMessageNotificationSettings.RECIPIENT_AGENT,
        )
        cls.preferences.stages.add(cls.stage)

    def setUp(self):
        # Keep database writes real, but prevent external delivery.
        # enterContext restores each patched function automatically after the test.
        self.push = self.enterContext(patch("apis.notification.notification_utils._send_onesignal_push"))
        # These payload functions do not currently broadcast; guard the channel boundary too.
        channel_layer = self.enterContext(patch("apis.notification.notification_utils.get_channel_layer"))
        channel_layer.return_value.group_send = AsyncMock()
        # No message row is needed: notification creation only reads these fields.
        self.message = Message(conversation=self.conversation, text="Please help", ttype="text", from_me=False)

    def new_message(self, **kwargs):
        # Exercise the production entry point with this test's conversation and incoming message.
        return create_new_message_notifications_payload(self.conversation, self.message, **kwargs)

    def assert_recipients(self, payload, users, title, message):
        expected_ids = [user.id for user in users]
        records = Notification.objects.filter(conversation=self.conversation)
        # Database recipients and returned payload must agree, with no extra or duplicate alerts.
        self.assertCountEqual(records.values_list("user_id", flat=True), expected_ids)
        self.assertCountEqual(payload["notification_event"]["target_user_ids"], expected_ids)
        self.assertCountEqual([row["id"] for row in payload["notifications"]], records.values_list("id", flat=True))
        self.assertEqual(payload["notification_event"]["conversation_id"], self.conversation.id)
        self.assertEqual(payload["notification_event"]["title"], title)
        self.assertEqual(payload["notification_event"]["message"], message)
        # Every notification starts unread and points back to the correct conversation.
        for record in records:
            self.assertFalse(record.seen)
            self.assertEqual(record.conversation_ids, [self.conversation.id])
            self.assertEqual(record.title, title)
            self.assertEqual(record.message, message)
        # Pushes may be grouped; collect recipients across all calls without assuming order.
        self.assertTrue(self.push.called)
        self.assertCountEqual(
            [user.id for call in self.push.call_args_list for user in call.args[3]], expected_ids,
        )

    def assert_no_notification(self, payload):
        # Suppression must leave no payload, saved notification, or push attempt.
        self.assertEqual(payload, {"notifications": [], "notification_event": None})
        self.assertFalse(Notification.objects.exists())
        self.push.assert_not_called()

    def test_new_message_notifies_only_assigned_agent(self):
        # Both assignments exist, but the configured recipient is the agent.
        self.assert_recipients(self.new_message(), [self.agent], "New message from Customer", "Please help")

    def test_new_message_notifies_only_contact_owner_when_configured(self):
        # Switching the setting selects the owner even though an agent is also assigned.
        self.preferences.recipient = NewMessageNotificationSettings.RECIPIENT_CONTACT_OWNER
        self.preferences.save()
        self.assert_recipients(self.new_message(), [self.owner], "New message from Customer", "Please help")

    def test_unassigned_fallback_notifies_active_company_users_even_if_assignee_setting_disabled(self):
        # Fallback has its own switch and works independently of assignee notifications.
        # No dispatcher config is needed when dispatching is disabled.
        self.conversation.agent = None
        self.conversation.contact_owner = None
        self.preferences.enabled = False
        self.preferences.notify_all_users_on_new_conversation = True
        self.preferences.save()
        self.assert_recipients(self.new_message(), [self.agent, self.owner], "New message from Customer", "Please help")

    def test_unassigned_fallback_requires_opt_in(self):
        # An unassigned conversation alone is insufficient: fallback defaults to off.
        self.conversation.agent = None
        self.conversation.contact_owner = None
        self.assert_no_notification(self.new_message())

    def test_enabled_dispatcher_suppresses_unassigned_fallback(self):
        # Enabling dispatching prevents the all-user fallback, even when opted in.
        self.conversation.agent = None
        self.conversation.contact_owner = None
        self.preferences.notify_all_users_on_new_conversation = True
        self.preferences.save()
        ChatroomDispatchConfig.objects.create(company=self.company, is_enabled=True)
        self.assert_no_notification(self.new_message())

    def test_fallback_does_not_broadcast_when_either_assignment_exists(self):
        self.preferences.enabled = False
        self.preferences.notify_all_users_on_new_conversation = True
        self.preferences.save()
        # Disable direct alerts above to isolate fallback: either assignment blocks it.
        for agent, owner in ((self.agent, None), (None, self.owner)):
            with self.subTest(agent=agent, owner=owner):
                self.conversation.agent = agent
                self.conversation.contact_owner = owner
                self.assert_no_notification(self.new_message())

    def test_mentions_notify_only_active_mentioned_company_users_once_excluding_actor(self):
        # Mentions do not require stage notification rules or new-message settings.
        self.preferences.delete()
        # Repeat the owner to check deduplication; the actor, inactive user, and outsider
        # must receive nothing, leaving exactly one notification for the owner.
        payload = create_chatroom_notifications_payload(
            self.conversation, actor=self.agent,
            mentioned_user_ids=[self.owner.id, self.owner.id, self.agent.id, self.inactive.id, self.outsider.id],
        )
        title = "Agent mentioned you in a note on Customer"
        self.assert_recipients(payload, [self.owner], title, title)
