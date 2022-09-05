import {
  describe,
  test,
  assert,
  clearStore,
} from "matchstick-as/assembly/index";

import {
  handleTransfer,
  HMT_STATISTICS_ENTITY_ID,
} from "../../src/mapping/hm-token";
import { createTransferEvent } from "./fixtures";

describe("HMToken entity", () => {
  test("Should properly calculate Transfer event in statistics", () => {
    let transfer1 = createTransferEvent(
      "0xD979105297fB0eee83F7433fC09279cb5B94fFC6",
      "0x92a2eEF7Ff696BCef98957a0189872680600a959",
      1
    );
    let transfer2 = createTransferEvent(
      "0xD979105297fB0eee83F7433fC09279cb5B94fFC6",
      "0x92a2eEF7Ff696BCef98957a0189872680600a959",
      2
    );

    handleTransfer(transfer1);
    handleTransfer(transfer2);

    assert.fieldEquals(
      "HMTokenStatistics",
      HMT_STATISTICS_ENTITY_ID,
      "totalTransferEventCount",
      "2"
    );
    assert.fieldEquals(
      "HMTokenStatistics",
      HMT_STATISTICS_ENTITY_ID,
      "totalValueTransfered",
      "3"
    );

    clearStore();
  });
});
