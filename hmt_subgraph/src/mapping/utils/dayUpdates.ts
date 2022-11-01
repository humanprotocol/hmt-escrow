/* eslint-disable prefer-const */
import { BigInt, ethereum } from "@graphprotocol/graph-ts";
import { Launched } from "../../../generated/EscrowFactory/EscrowFactory";
import { EventDayData } from "../../../generated/schema";
import {
  IntermediateStorage,
  Pending,
  BulkTransfer,
} from "../../../generated/templates/Escrow/Escrow";

const ZERO_BI = BigInt.fromI32(0);

function getEventDayData(event: ethereum.Event): EventDayData {
  let timestamp = event.block.timestamp.toI32();
  let dayID = timestamp / 86400;
  let dayStartTimestamp = dayID * 86400;

  let eventDayData = EventDayData.load(dayID.toString());
  if (eventDayData === null) {
    eventDayData = new EventDayData(dayID.toString());
    eventDayData.timestamp = dayStartTimestamp;
    eventDayData.dailyBulkTransferEvents = ZERO_BI;
    eventDayData.dailyIntermediateStorageEvents = ZERO_BI;
    eventDayData.dailyPendingEvents = ZERO_BI;
    eventDayData.dailyEscrowAmounts = ZERO_BI;
  }
  return eventDayData;
}

export function updateIntermediateStorageEventDayData(
  event: IntermediateStorage
): EventDayData {
  const eventDayData = getEventDayData(event);
  // @ts-ignore
  eventDayData.dailyIntermediateStorageEvents += BigInt.fromI32(1);
  eventDayData.save();

  return eventDayData;
}

export function updatePendingEventDayData(event: Pending): EventDayData {
  const eventDayData = getEventDayData(event);
  // @ts-ignore
  eventDayData.dailyPendingEvents += BigInt.fromI32(1);
  eventDayData.save();

  return eventDayData;
}

export function updateBulkTransferEventDayData(
  event: BulkTransfer
): EventDayData {
  const eventDayData = getEventDayData(event);
  // @ts-ignore
  eventDayData.dailyBulkTransferEvents += BigInt.fromI32(1);
  eventDayData.save();

  return eventDayData;
}

export function updateEscrowAmountDayData(event: Launched): EventDayData {
  const eventDayData = getEventDayData(event);
  // @ts-ignore
  eventDayData.dailyEscrowAmounts += BigInt.fromI32(1);
  eventDayData.save();

  return eventDayData;
}
