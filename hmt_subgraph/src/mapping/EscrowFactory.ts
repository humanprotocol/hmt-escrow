import { Launched } from "../../generated/EscrowFactory/EscrowFactory";
import { LaunchedEscrow } from "../../generated/schema";
import { Escrow } from "../../generated/templates";

export function handleLaunched(event: Launched): void {
  // Entities only exist after they have been saved to the store;
  let entity = new LaunchedEscrow(event.params.escrow.toHex());

  // Entity fields can be set based on event parameters
  entity.eip20 = event.params.eip20;
  entity.from = event.transaction.from;
  entity.timestamp = event.block.timestamp;

  // Entities can be written to the store with `.save()`
  entity.save();
  Escrow.create(event.params.escrow);
}
