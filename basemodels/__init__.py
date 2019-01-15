import uuid
from schematics.models import Model, ValidationError
from schematics.types import StringType, DecimalType, BooleanType, IntType, DictType, ListType, URLType, FloatType, \
    UUIDType, ModelType


class TaskData(Model):
    """ objects within taskdata list in Manifest """
    task_key = UUIDType(required=True)
    datapoint_uri = URLType(required=True, min_length=10)
    datapoint_hash = StringType(required=True, min_length=10)


class Manifest(Model):
    """ The manifest description. """
    job_mode = StringType(
        required=True, choices=["batch", "online", "instant_delivery"])
    job_api_key = UUIDType(default=uuid.uuid4)
    job_id = UUIDType(default=uuid.uuid4)
    job_total_tasks = IntType()

    requester_restricted_answer_set = DictType(DictType(StringType))
    requester_description = StringType()
    requester_max_repeats = IntType(default=100)
    requester_min_repeats = IntType(default=1)
    requester_question = DictType(StringType)
    requester_question_example = URLType()
    unsafe_content = BooleanType(default=False)
    task_bid_price = DecimalType(required=True)
    oracle_stake = DecimalType(required=True)
    expiration_date = IntType()
    requester_accuracy_target = FloatType(default=.1)
    manifest_smart_bounty_addr = StringType()
    minimum_trust_server = FloatType(default=.1)
    minimum_trust_client = FloatType(default=.1)
    recording_oracle_addr = StringType(required=True)
    reputation_oracle_addr = StringType(required=True)
    reputation_agent_addr = StringType(required=True)
    requester_pgp_public_key = StringType()

    # Future TODO: replace with KV lookup on recording_oracle_addr
    # NOTE: URLType fails without TLD (examples: http://localhost/,
    #       http://exchange/, etc), so using StringType instead.
    ro_uri = StringType()
    repo_uri = StringType()

    batch_result_delivery_webhook = URLType()
    online_result_delivery_webhook = URLType()
    instant_result_delivery_webhook = URLType()
    request_type = StringType(
        required=True,
        choices=[
            "image_label_binary", "image_label_multiple_choice_one_option",
            "image_label_multiple_choice_multiple_options", "text_free_entry",
            "text_multiple_choice_one_option",
            "text_multiple_choice_multiple_options",
            "image_label_area_select_one_option",
            "image_label_area_select_multiple_options",
            "image_label_area_adjust"
        ])
    # if taskdata is directly provided
    taskdata = ListType(ModelType(TaskData))  # ListType(DictType(StringType))

    # if taskdata is separately stored
    taskdata_uri = URLType()

    def validate_taskdata_uri(self, data, value):
        if data.get('taskdata') and len(
                data.get('taskdata')) > 0 and data.get('taskdata_uri'):
            raise ValidationError(
                u'Specify only one of taskdata {} or taskdata_uri {}'.format(
                    data.get('taskdata'), data.get('taskdata_uri')))
        return value

    validate_taskdata = validate_taskdata_uri
