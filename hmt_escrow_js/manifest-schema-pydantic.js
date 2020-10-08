module.exports = {
  "title": "Manifest",
  "description": "The manifest description. ",
  "type": "object",
  "properties": {
    "job_mode": {
      "title": "Job Mode",
      "anyOf": [
        {
          "const": "batch",
          "type": "string"
        },
        {
          "const": "online",
          "type": "string"
        },
        {
          "const": "instant_delivery",
          "type": "string"
        }
      ]
    },
    "job_api_key": {
      "title": "Job Api Key",
      "type": "string",
      "format": "uuid"
    },
    "job_id": {
      "title": "Job Id",
      "type": "string",
      "format": "uuid"
    },
    "job_total_tasks": {
      "title": "Job Total Tasks",
      "type": "integer"
    },
    "multi_challenge_manifests": {
      "title": "Multi Challenge Manifests",
      "type": "array",
      "items": {
        "$ref": "#/definitions/NestedManifest"
      }
    },
    "request_type": {
      "$ref": "#/definitions/BaseJobTypesEnum"
    },
    "requester_restricted_answer_set": {
      "title": "Requester Restricted Answer Set",
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      }
    },
    "requester_description": {
      "title": "Requester Description",
      "type": "string"
    },
    "requester_max_repeats": {
      "title": "Requester Max Repeats",
      "default": 100,
      "type": "integer"
    },
    "requester_min_repeats": {
      "title": "Requester Min Repeats",
      "default": 1,
      "type": "integer"
    },
    "requester_question": {
      "title": "Requester Question",
      "type": "object",
      "additionalProperties": {
        "type": "string"
      }
    },
    "requester_question_example": {
      "title": "Requester Question Example",
      "anyOf": [
        {
          "type": "string",
          "minLength": 1,
          "maxLength": 2083,
          "format": "uri"
        },
        {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2083,
            "format": "uri"
          }
        }
      ]
    },
    "unsafe_content": {
      "title": "Unsafe Content",
      "default": false,
      "type": "boolean"
    },
    "task_bid_price": {
      "title": "Task Bid Price",
      "type": "number"
    },
    "oracle_stake": {
      "title": "Oracle Stake",
      "type": "number"
    },
    "expiration_date": {
      "title": "Expiration Date",
      "type": "integer"
    },
    "requester_accuracy_target": {
      "title": "Requester Accuracy Target",
      "default": 0.1,
      "type": "number"
    },
    "manifest_smart_bounty_addr": {
      "title": "Manifest Smart Bounty Addr",
      "type": "string"
    },
    "hmtoken_addr": {
      "title": "Hmtoken Addr",
      "type": "string"
    },
    "minimum_trust_server": {
      "title": "Minimum Trust Server",
      "default": 0.1,
      "type": "number"
    },
    "minimum_trust_client": {
      "title": "Minimum Trust Client",
      "default": 0.1,
      "type": "number"
    },
    "recording_oracle_addr": {
      "title": "Recording Oracle Addr",
      "type": "string"
    },
    "reputation_oracle_addr": {
      "title": "Reputation Oracle Addr",
      "type": "string"
    },
    "reputation_agent_addr": {
      "title": "Reputation Agent Addr",
      "type": "string"
    },
    "requester_pgp_public_key": {
      "title": "Requester Pgp Public Key",
      "type": "string"
    },
    "ro_uri": {
      "title": "Ro Uri",
      "type": "string"
    },
    "repo_uri": {
      "title": "Repo Uri",
      "type": "string"
    },
    "batch_result_delivery_webhook": {
      "title": "Batch Result Delivery Webhook",
      "minLength": 1,
      "maxLength": 2083,
      "format": "uri",
      "type": "string"
    },
    "online_result_delivery_webhook": {
      "title": "Online Result Delivery Webhook",
      "minLength": 1,
      "maxLength": 2083,
      "format": "uri",
      "type": "string"
    },
    "instant_result_delivery_webhook": {
      "title": "Instant Result Delivery Webhook",
      "minLength": 1,
      "maxLength": 2083,
      "format": "uri",
      "type": "string"
    },
    "request_config": {
      "$ref": "#/definitions/RequestConfig"
    },
    "taskdata": {
      "title": "Taskdata",
      "type": "array",
      "items": {
        "$ref": "#/definitions/TaskData"
      }
    },
    "taskdata_uri": {
      "title": "Taskdata Uri",
      "minLength": 1,
      "maxLength": 2083,
      "format": "uri",
      "type": "string"
    },
    "groundtruth_uri": {
      "title": "Groundtruth Uri",
      "minLength": 1,
      "maxLength": 2083,
      "format": "uri",
      "type": "string"
    },
    "groundtruth": {
      "title": "Groundtruth",
      "type": "string"
    },
    "internal_config": {
      "$ref": "#/definitions/InternalConfig"
    },
    "confcalc_configuration_id": {
      "title": "Confcalc Configuration Id",
      "type": "string"
    },
    "restricted_audience": {
      "title": "Restricted Audience",
      "type": "object",
      "additionalProperties": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                  "type": "number"
                }
              }
            }
          }
        ]
      }
    },
    "webhook": {
      "$ref": "#/definitions/Webhook"
    }
  },
  "required": [
    "job_mode",
    "request_type",
    "task_bid_price",
    "oracle_stake",
    "recording_oracle_addr",
    "reputation_oracle_addr",
    "reputation_agent_addr"
  ],
  "definitions": {
    "BaseJobTypesEnum": {
      "title": "BaseJobTypesEnum",
      "description": "An enumeration.",
      "enum": [
        "image_label_binary",
        "image_label_multiple_choice",
        "text_free_entry",
        "text_multiple_choice_one_option",
        "text_multiple_choice_multiple_options",
        "image_label_area_adjust",
        "image_label_area_select",
        "image_label_single_polygon",
        "image_label_multiple_polygons",
        "image_label_semantic_segmentation_one_option",
        "image_label_semantic_segmentation_multiple_options",
        "image_label_text",
        "multi_challenge"
      ],
      "type": "string"
    },
    "ShapeTypes": {
      "title": "ShapeTypes",
      "description": "An enumeration.",
      "enum": [
        "point",
        "bounding_box",
        "polygon"
      ],
      "type": "string"
    },
    "RequestConfig": {
      "title": "RequestConfig",
      "description": "definition of the request_config object in manifest ",
      "type": "object",
      "properties": {
        "version": {
          "title": "Version",
          "default": 0,
          "type": "integer"
        },
        "shape_type": {
          "$ref": "#/definitions/ShapeTypes"
        },
        "min_points": {
          "title": "Min Points",
          "type": "integer"
        },
        "max_points": {
          "title": "Max Points",
          "type": "integer"
        },
        "min_shapes_per_image": {
          "title": "Min Shapes Per Image",
          "type": "integer"
        },
        "max_shapes_per_image": {
          "title": "Max Shapes Per Image",
          "type": "integer"
        },
        "restrict_to_coords": {
          "title": "Restrict To Coords",
          "type": "boolean"
        },
        "minimum_selection_area_per_shape": {
          "title": "Minimum Selection Area Per Shape",
          "type": "integer"
        },
        "multiple_choice_max_choices": {
          "title": "Multiple Choice Max Choices",
          "default": 1,
          "type": "integer"
        },
        "multiple_choice_min_choices": {
          "title": "Multiple Choice Min Choices",
          "default": 1,
          "type": "integer"
        }
      }
    },
    "Webhook": {
      "title": "Webhook",
      "description": "Model for webhook configuration ",
      "type": "object",
      "properties": {
        "webhook_id": {
          "title": "Webhook Id",
          "type": "string",
          "format": "uuid"
        },
        "chunk_completed": {
          "title": "Chunk Completed",
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "job_completed": {
          "title": "Job Completed",
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "webhook_id"
      ]
    },
    "NestedManifest": {
      "title": "NestedManifest",
      "description": "The nested manifest description for multi_challenge jobs ",
      "type": "object",
      "properties": {
        "job_id": {
          "title": "Job Id",
          "type": "string",
          "format": "uuid"
        },
        "request_type": {
          "$ref": "#/definitions/BaseJobTypesEnum"
        },
        "requester_restricted_answer_set": {
          "title": "Requester Restricted Answer Set",
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            }
          }
        },
        "requester_description": {
          "title": "Requester Description",
          "type": "string"
        },
        "requester_max_repeats": {
          "title": "Requester Max Repeats",
          "default": 100,
          "type": "integer"
        },
        "requester_min_repeats": {
          "title": "Requester Min Repeats",
          "default": 1,
          "type": "integer"
        },
        "requester_question": {
          "title": "Requester Question",
          "type": "object",
          "additionalProperties": {
            "type": "string"
          }
        },
        "requester_question_example": {
          "title": "Requester Question Example",
          "anyOf": [
            {
              "type": "string",
              "minLength": 1,
              "maxLength": 2083,
              "format": "uri"
            },
            {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 2083,
                "format": "uri"
              }
            }
          ]
        },
        "unsafe_content": {
          "title": "Unsafe Content",
          "default": false,
          "type": "boolean"
        },
        "requester_accuracy_target": {
          "title": "Requester Accuracy Target",
          "default": 0.1,
          "type": "number"
        },
        "request_config": {
          "$ref": "#/definitions/RequestConfig"
        },
        "groundtruth_uri": {
          "title": "Groundtruth Uri",
          "minLength": 1,
          "maxLength": 2083,
          "format": "uri",
          "type": "string"
        },
        "groundtruth": {
          "title": "Groundtruth",
          "type": "string"
        },
        "confcalc_configuration_id": {
          "title": "Confcalc Configuration Id",
          "type": "string"
        },
        "webhook": {
          "$ref": "#/definitions/Webhook"
        }
      },
      "required": [
        "request_type"
      ]
    },
    "TaskData": {
      "title": "TaskData",
      "description": "objects within taskdata list in Manifest ",
      "type": "object",
      "properties": {
        "task_key": {
          "title": "Task Key",
          "type": "string",
          "format": "uuid"
        },
        "datapoint_uri": {
          "title": "Datapoint Uri",
          "minLength": 1,
          "maxLength": 2083,
          "format": "uri",
          "type": "string"
        },
        "datapoint_hash": {
          "title": "Datapoint Hash",
          "minLength": 10,
          "strip_whitespace": true,
          "type": "string"
        }
      },
      "required": [
        "task_key",
        "datapoint_uri",
        "datapoint_hash"
      ]
    },
    "InternalConfig": {
      "title": "InternalConfig",
      "description": "discarded from incoming manifests ",
      "type": "object",
      "properties": {
        "exchange": {
          "title": "Exchange",
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "integer"
              },
              {
                "type": "number"
              }
            ]
          }
        },
        "reco": {
          "title": "Reco",
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "integer"
              },
              {
                "type": "number"
              }
            ]
          }
        },
        "repo": {
          "title": "Repo",
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "integer"
              },
              {
                "type": "number"
              }
            ]
          }
        },
        "other": {
          "title": "Other",
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "integer"
              },
              {
                "type": "number"
              }
            ]
          }
        },
        "mitl": {
          "title": "Mitl",
          "type": "object",
          "additionalProperties": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "integer"
              },
              {
                "type": "number"
              },
              {
                "type": "object",
                "additionalProperties": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "integer"
                    },
                    {
                      "type": "number"
                    }
                  ]
                }
              }
            ]
          }
        }
      }
    }
  }
}