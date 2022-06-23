import { BigInt } from "@graphprotocol/graph-ts";
import {
  BulkTransfer,
  IntermediateStorage,
  Pending,
} from "../../generated/templates/Escrow/Escrow";
import { BulkTransferEvent, ISEvent, PEvent } from "../../generated/schema";

export function handleIntermediateStorage(event: IntermediateStorage): void {
  // Entities can be loaded from the store using a string ID; this ID
  // needs to be unique across all entities of the same type
  let id = event.transaction.from.toHex() + event.address.toHex();
  let entity = ISEvent.load(id);

  // Entities only exist after they have been saved to the store;
  // `null` checks allow to create entities on demand
  if (!entity) {
    entity = new ISEvent(id);

    // Entity fields can be set using simple assignments
    entity.count = BigInt.fromI32(0);
  }

  // BigInt and BigDecimal math are supported
  // @ts-ignore
  entity.count = entity.count + BigInt.fromI32(1);

  // Entity fields can be set based on event parameters
  entity._url = event.params._url;
  entity._hash = event.params._hash;

  // Entities can be written to the store with `.save()`
  entity.save();
}

export function handlePending(event: Pending): void {
  // Entities can be loaded from the store using a string ID; this ID
  // needs to be unique across all entities of the same type
  let id = event.transaction.from.toHex() + event.address.toHex();
  let entity = PEvent.load(id);

  // Entities only exist after they have been saved to the store;
  // `null` checks allow to create entities on demand
  if (!entity) {
    entity = new PEvent(id);
    // Entity fields can be set using simple assignments
    entity.count = BigInt.fromI32(0);
  }

  // BigInt and BigDecimal math are supported
  // @ts-ignore
  entity.count = entity.count + BigInt.fromI32(1);

  // Entity fields can be set based on event parameters
  entity._url = event.params.manifest;
  entity._hash = event.params.hash;

  // Entities can be written to the store with `.save()`
  entity.save();
}

export function handleBulkTransfer(event: BulkTransfer): void {
  let entity = BulkTransferEvent.load(
    event.transaction.hash.toHex() + "-" + event.logIndex.toString()
  );

  if (!entity) {
    entity = new BulkTransferEvent(
      event.transaction.hash.toHex() + "-" + event.logIndex.toString()
    );
  }

  entity.escrow = event.address;

  entity.bulkCount = event.params._bulkCount;
  entity.txId = event.params._txId;

  entity.block = event.block.number;
  entity.timestamp = event.block.timestamp;
  entity.transaction = event.transaction.hash;

  entity.save();
}
