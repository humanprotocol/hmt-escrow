import { newMockEvent } from "matchstick-as/assembly/index";
import { ethereum, BigInt } from "@graphprotocol/graph-ts";

import {
  IntermediateStorage,
  Pending,
  BulkTransfer,
} from "../../generated/templates/Escrow/Escrow";

export function createISEvent(url: string, hash: string): IntermediateStorage {
  let newIntermediateStorageEvent = changetype<IntermediateStorage>(
    newMockEvent()
  );
  newIntermediateStorageEvent.parameters = new Array();
  let urlParam = new ethereum.EventParam(
    "_url",
    ethereum.Value.fromString(url)
  );
  let hashParam = new ethereum.EventParam(
    "_hash",
    ethereum.Value.fromString(hash)
  );

  newIntermediateStorageEvent.parameters.push(urlParam);
  newIntermediateStorageEvent.parameters.push(hashParam);

  return newIntermediateStorageEvent;
}

export function createPendingEvent(manifest: string, hash: string): Pending {
  let newPendingEvent = changetype<Pending>(newMockEvent());
  newPendingEvent.parameters = new Array();
  let manifestParam = new ethereum.EventParam(
    "manifest",
    ethereum.Value.fromString(manifest)
  );
  let hashParam = new ethereum.EventParam(
    "hash",
    ethereum.Value.fromString(hash)
  );

  newPendingEvent.parameters.push(manifestParam);
  newPendingEvent.parameters.push(hashParam);

  return newPendingEvent;
}

export function createBulkTransferEvent(
  txId: i32,
  bulkCount: i32,
  timestamp: BigInt
): BulkTransfer {
  let newBTEvent = changetype<BulkTransfer>(newMockEvent());
  newBTEvent.parameters = new Array();
  newBTEvent.block.timestamp = timestamp;
  let txIdParam = new ethereum.EventParam(
    "_txId",
    ethereum.Value.fromI32(txId)
  );
  let bulkCountParam = new ethereum.EventParam(
    "hash",
    ethereum.Value.fromI32(bulkCount)
  );

  newBTEvent.parameters.push(txIdParam);
  newBTEvent.parameters.push(bulkCountParam);

  return newBTEvent;
}
