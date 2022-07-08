import { newMockEvent } from "matchstick-as/assembly/index";
import { Address, ethereum, BigInt } from "@graphprotocol/graph-ts";

import { Transfer, Approval } from "../../generated/HMToken/HMToken";

export function createTransferEvent(from: string, to: string, value: i32): Transfer {
  let transferEvent = changetype<Transfer>(newMockEvent());
  transferEvent.parameters = new Array();
  let fromParam = new ethereum.EventParam("_from", ethereum.Value.fromAddress(Address.fromString(from)));
  let toParam = new ethereum.EventParam("_to", ethereum.Value.fromAddress(Address.fromString(to)));
  let valueParam = new ethereum.EventParam("_value", ethereum.Value.fromI32(value));

  transferEvent.parameters.push(fromParam);
  transferEvent.parameters.push(toParam);
  transferEvent.parameters.push(valueParam);

  return transferEvent;
}

export function createApprovalEvent(spender: string, owner: string, value: i32): Approval {
  let approvalEvent = changetype<Approval>(newMockEvent());
  approvalEvent.parameters = new Array();
  let ownerParam = new ethereum.EventParam("_spender", ethereum.Value.fromAddress(Address.fromString(spender)));
  let spenderParam = new ethereum.EventParam("_owner", ethereum.Value.fromAddress(Address.fromString(owner)));
  let valueParam = new ethereum.EventParam("_value", ethereum.Value.fromI32(value));

  approvalEvent.parameters.push(ownerParam);
  approvalEvent.parameters.push(spenderParam);
  approvalEvent.parameters.push(valueParam);

  return approvalEvent;
}
