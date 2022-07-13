import { Address, BigInt } from "@graphprotocol/graph-ts";
import {
  Approval,
  Transfer,
  BulkApproval,
  BulkTransfer,
} from "../../generated/HMToken/HMToken";
import {
  HMBulkTransferEvent,
  HMTransferEvent,
  HMBulkApprovalEvent,
  HMApprovalEvent,
  HMTokenStatistics,
} from "../../generated/schema";

export const HMT_STATISTICS_ENTITY_ID = 'hmt-statistics-1';

function constructStatsEntity(tokenAddress: Address): HMTokenStatistics {
  const entity = new HMTokenStatistics(HMT_STATISTICS_ENTITY_ID);

  entity.transferEventCount = BigInt.fromI32(0);
  entity.bulkTransferEventCount = BigInt.fromI32(0);
  entity.approvalEventCount = BigInt.fromI32(0);
  entity.bulkApprovalEventCount = BigInt.fromI32(0);
  entity.token = tokenAddress;

  return entity;
}

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

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);

  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }

  statsEntity.transferEventCount += BigInt.fromI32(1);

  statsEntity.save();
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

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);

  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }

  statsEntity.bulkTransferEventCount += BigInt.fromI32(1);

  statsEntity.save();
}

export function handleApproval(event: Approval): void {
  let entity = HMApprovalEvent.load(
    event.transaction.hash.toHex() + "-" + event.logIndex.toString()
  );
  if (!entity) {
    entity = new HMApprovalEvent(
      event.transaction.hash.toHex() + "-" + event.logIndex.toString()
    );
  }
  entity.token = event.address;
  entity.owner = event.params._owner;
  entity.spender = event.params._spender;
  entity.value = event.params._value;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  entity.save();

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);

  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }

  statsEntity.approvalEventCount += BigInt.fromI32(1);

  statsEntity.save();
}

export function handleBulkApproval(event: BulkApproval): void {
  let entity = HMBulkApprovalEvent.load(
    event.transaction.hash.toHex() + "-" + event.logIndex.toString()
  );

  if (!entity) {
    entity = new HMBulkApprovalEvent(
      event.transaction.hash.toHex() + "-" + event.logIndex.toString()
    );
  }

  entity.bulkCount = event.params._bulkCount;
  entity.txId = event.params._txId;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  entity.save();

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);

  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }

  statsEntity.bulkApprovalEventCount += BigInt.fromI32(1);

  statsEntity.save();
}
