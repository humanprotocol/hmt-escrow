import { describe, test, assert, clearStore } from "matchstick-as/assembly/index";
import { store, BigInt } from "@graphprotocol/graph-ts"


import { HMTransferEvent } from "../../generated/schema";
import { Transfer, Approval } from "../../generated/HMToken/HMToken";
import { handleTransfer, handleApproval, HMT_STATISTICS_ENTITY_ID } from "../../src/mapping/hm-token";
import { createTransferEvent, createApprovalEvent } from './fixtures';

describe("HMToken entity", () => {
  test("Should properly calculate Transfer event in statistics", () => {
    let transfer1 = createTransferEvent("0xD979105297fB0eee83F7433fC09279cb5B94fFC6", "0x92a2eEF7Ff696BCef98957a0189872680600a959", 1);
    let transfer2 = createTransferEvent("0xD979105297fB0eee83F7433fC09279cb5B94fFC6", "0x92a2eEF7Ff696BCef98957a0189872680600a959", 2);

    handleTransfer(transfer1);
    handleTransfer(transfer2);

    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "transferEventCount", '2');
    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "bulkTransferEventCount", '0');
    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "approvalEventCount", '0');
    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "bulkApprovalEventCount", '0');

    clearStore();
  });

  test("Should properly calculate Approval event in statistics", () => {
    let transfer1 = createApprovalEvent("0xD979105297fB0eee83F7433fC09279cb5B94fFC6", "0x92a2eEF7Ff696BCef98957a0189872680600a959", 1);
    let transfer2 = createApprovalEvent("0xD979105297fB0eee83F7433fC09279cb5B94fFC6", "0x92a2eEF7Ff696BCef98957a0189872680600a959", 2);

    handleApproval(transfer1);
    handleApproval(transfer2);

    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "transferEventCount", '0');
    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "bulkTransferEventCount", '0');
    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "approvalEventCount", '2');
    assert.fieldEquals("HMTokenStatistics", HMT_STATISTICS_ENTITY_ID, "bulkApprovalEventCount", '0');

    clearStore();
  });
});
