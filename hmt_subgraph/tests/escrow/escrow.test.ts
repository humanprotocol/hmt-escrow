import { describe, test, assert, clearStore } from "matchstick-as/assembly/index";
import { store, BigInt } from "@graphprotocol/graph-ts"


import { ISEvent } from "../../generated/schema";
import { IntermediateStorage, Pending, BulkTransfer } from "../../generated/templates/Escrow/Escrow";
import { handleIntermediateStorage, handlePending, handleBulkTransfer, STATISTICS_ENTITY_ID } from "../../src/mapping/Escrow";
import { createISEvent, createPendingEvent, createBulkTransferEvent } from './fixtures';

describe("Generic Entity case", () => {
  test("Should correctly get ISEvents entity details", () => {
    const DUMMY_ID = "0x0-0x0";

    const intermediateStorageEvent = new ISEvent(DUMMY_ID);
    intermediateStorageEvent.count = BigInt.fromString('1');
    intermediateStorageEvent._url = "test.com";
    intermediateStorageEvent._hash = "testhash";

    intermediateStorageEvent.save();
    assert.fieldEquals("ISEvent", DUMMY_ID, "count", '1');
    assert.fieldEquals("ISEvent", DUMMY_ID, "_url", "test.com");
    assert.fieldEquals("ISEvent", DUMMY_ID, "_hash", "testhash");

    store.remove("ISEvent", DUMMY_ID);
  });
})

describe("EscrowStatistics entity", () => {
  test("Should properly calculate IntermediateStorage event in statistics", () => {
    let newIS = createISEvent("test.com", "is_hash_1");
    let newIS1 = createISEvent("test.com", "is_hash_1");

    handleIntermediateStorage(newIS);
    handleIntermediateStorage(newIS1);

    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "pendingEventCount", '0');
    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "intermediateStorageEventCount", '2');
    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "bulkTransferEventCount", '0');

    clearStore();
  });

  test("Should properly calculate Pending event in statistics", () => {
    let newPending1 = createPendingEvent("test.com", "is_hash_1");
    let newPending2 = createPendingEvent("test.com", "is_hash_1");

    handlePending(newPending1);
    handlePending(newPending2);

    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "pendingEventCount", '2');
    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "intermediateStorageEventCount", '0');
    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "bulkTransferEventCount", '0');

    clearStore();
  });

  test("Should properly calculate BulkTransfser event in statistics", () => {
    let bulkEvent1 = createBulkTransferEvent(1, 5);
    let bulkEvent2 = createBulkTransferEvent(2, 4);

    handleBulkTransfer(bulkEvent1);
    handleBulkTransfer(bulkEvent2);

    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "pendingEventCount", '0');
    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "intermediateStorageEventCount", '0');
    assert.fieldEquals("EscrowStatistics", STATISTICS_ENTITY_ID, "bulkTransferEventCount", '2');

    clearStore();
  });
});
