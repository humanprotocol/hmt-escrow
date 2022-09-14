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

export const HMT_STATISTICS_ENTITY_ID = "hmt-statistics-id";

function constructStatsEntity(tokenAddress: Address): HMTokenStatistics {
  const entity = new HMTokenStatistics(HMT_STATISTICS_ENTITY_ID);

  entity.totalTransferEventCount = BigInt.fromI32(0);
  entity.totalApprovalEventCount = BigInt.fromI32(0);
  entity.totalBulkApprovalEventCount = BigInt.fromI32(0);
  entity.totalBulkTransferEventCount = BigInt.fromI32(0);
  entity.totalValueTransfered = BigInt.fromI32(0);
  entity.token = tokenAddress;

  return entity;
}

export function handleTransfer(event: Transfer): void {
  const id = `${event.transaction.hash.toHex()}-${event.logIndex.toString()}-${
    event.block.timestamp
  }`;

  let entity = new HMTransferEvent(id);

  entity.token = event.address;
  entity.from = event.params._from;
  entity.to = event.params._to;
  entity.value = event.params._value;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);

  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }
  //@ts-ignore
  entity.count = statsEntity.totalTransferEventCount + BigInt.fromI32(1);

  //@ts-ignore
  statsEntity.totalTransferEventCount += BigInt.fromI32(1);
  //@ts-ignore
  statsEntity.totalValueTransfered += event.params._value;

  statsEntity.save();

  entity.save();
}

export function handleBulkTransfer(event: BulkTransfer): void {
  const id = `${event.transaction.hash.toHex()}-${event.logIndex.toString()}-${
    event.block.timestamp
  }`;

  let entity = new HMBulkTransferEvent(id);

  entity.bulkCount = event.params._bulkCount;
  entity.txId = event.params._txId;
  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);
  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }
  //@ts-ignore
  entity.count = statsEntity.totalBulkTransferEventCount + BigInt.fromI32(1);

  //@ts-ignore
  statsEntity.totalBulkTransferEventCount += BigInt.fromI32(1);

  statsEntity.save();

  entity.save();
}

export function handleApproval(event: Approval): void {
  const id = `${event.transaction.hash.toHex()}-${event.logIndex.toString()}-${
    event.block.timestamp
  }`;

  let entity = new HMApprovalEvent(id);

  entity.token = event.address;
  entity.owner = event.params._owner;
  entity.spender = event.params._spender;
  entity.value = event.params._value;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);
  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }
  //@ts-ignore
  entity.count = statsEntity.totalApprovalEventCount + BigInt.fromI32(1);

  //@ts-ignore
  statsEntity.totalApprovalEventCount += BigInt.fromI32(1);

  statsEntity.save();

  entity.save();
}

export function handleBulkApproval(event: BulkApproval): void {
  const id = `${event.transaction.hash.toHex()}-${event.logIndex.toString()}-${
    event.block.timestamp
  }`;

  let entity = new HMBulkApprovalEvent(id);

  entity.bulkCount = event.params._bulkCount;
  entity.txId = event.params._txId;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  let statsEntity = HMTokenStatistics.load(HMT_STATISTICS_ENTITY_ID);
  if (!statsEntity) {
    statsEntity = constructStatsEntity(event.address);
  }
  //@ts-ignore
  entity.count = statsEntity.totalBulkApprovalEventCount + BigInt.fromI32(1);

  //@ts-ignore
  statsEntity.totalBulkApprovalEventCount += BigInt.fromI32(1);

  statsEntity.save();

  entity.save();
}
