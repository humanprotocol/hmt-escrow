import {
  Approval,
  Transfer,
  BulkApproval,
  BulkTransfer,
} from "../../generated/HMToken/HMToken";
import { HMBulkTransferEvent, HMTransferEvent } from "../../generated/schema";

export function handleTransfer(event: Transfer): void {
  let entity = HMTransferEvent.load(
    event.transaction.hash.toHex() + "-" + event.logIndex.toString()
  );
  if (!entity) {
    entity = new HMTransferEvent(
      event.transaction.hash.toHex() + "-" + event.logIndex.toString()
    );
  }
  entity.token = event.address;
  entity.from = event.params._from;
  entity.to = event.params._to;
  entity.value = event.params._value;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  entity.save();
}

export function handleBulkTransfer(event: BulkTransfer): void {
  let entity = HMBulkTransferEvent.load(
    event.transaction.hash.toHex() + "-" + event.logIndex.toString()
  );

  if (!entity) {
    entity = new HMBulkTransferEvent(
      event.transaction.hash.toHex() + "-" + event.logIndex.toString()
    );
  }

  entity.bulkCount = event.params._bulkCount;
  entity.txId = event.params._txId;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  entity.save();
}

export function handleBulkApproval(event: BulkApproval): void {}
export function handleApproval(event: Approval): void {}
