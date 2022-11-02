import { anyValue } from "@nomicfoundation/hardhat-chai-matchers/withArgs";
import { expect } from "chai";
import { ethers } from "hardhat";
import { Signer } from "ethers";
import { Escrow, HMToken, RewardPool, Staking } from "../typechain-types";

describe("Escrow", function () {
  const MOCK_URL = "http://google.com/fake";
  const MOCK_HASH = "kGKmnj9BRf";
  const BULK_MAX_COUNT = 100;

  enum Status {
    Launched = 0,
    Pending = 1,
    Partial = 2,
    Paid = 3,
    Complete = 4,
    Cancelled = 5,
  }

  let owner: Signer,
    launcher: Signer,
    reputationOracle: Signer,
    recordingOracle: Signer,
    externalAddress: Signer,
    restAccounts: Signer[],
    trustedHandlers: string[];

  let token: HMToken, escrow: Escrow, staking: Staking, rewardPool: RewardPool;

  let escrowFactory: Signer;

  const minimumStake = 2;
  const lockPeriod = 2;
  const rewardFee = 2;

  beforeEach(async () => {
    [
      owner,
      launcher,
      reputationOracle,
      recordingOracle,
      externalAddress,
      escrowFactory,
      ...restAccounts
    ] = await ethers.getSigners();
    trustedHandlers = [
      await reputationOracle.getAddress(),
      await recordingOracle.getAddress(),
    ];

    // Deploy HMTToken Contract
    const HMToken = await ethers.getContractFactory("HMToken");
    token = await HMToken.deploy(1000000000, "Human Token", 18, "HMT");

    // Deploy Staking Conract
    const Staking = await ethers.getContractFactory("Staking");
    staking = await Staking.deploy(
      token.address,
      await escrowFactory.getAddress(),
      minimumStake,
      lockPeriod
    );

    // Deploy Reward Pool Conract
    const RewardPool = await ethers.getContractFactory("RewardPool");
    rewardPool = await RewardPool.deploy(
      token.address,
      staking.address,
      rewardFee
    );

    // Configure RewardPool in Staking
    await staking.setRewardPool(rewardPool.address);

    // Deploy Escrow Contract
    const Escrow = await ethers.getContractFactory("Escrow");
    escrow = await Escrow.deploy(
      token.address,
      staking.address,
      await owner.getAddress(),
      5,
      trustedHandlers
    );
  });

  describe("deployment", () => {
    it("Should set the right token address", async () => {
      const result = await escrow.eip20();
      expect(result).to.equal(token.address);
    });

    it("Should set the right launched status", async () => {
      const result = await escrow.status();
      expect(result).to.equal(Status.Launched);
    });

    it("Should set the right escrow balance", async () => {
      const result = await escrow.connect(launcher).getBalance();
      expect(result.toString()).to.equal("0");
    });

    it("Should set the right contract creator", async () => {
      const result = await escrow.launcher();
      expect(result).to.equal(await owner.getAddress());
    });

    it("Should topup and return the right escrow balance", async () => {
      const amount = 1000;
      await token.connect(owner).transfer(escrow.address, amount);

      const result = await escrow.connect(launcher).getBalance();
      expect(result).to.equal(amount.toString());
    });
  });

  describe("abort", () => {
    describe("Validations", function () {
      beforeEach(async () => {
        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
        await escrow
          .connect(owner)
          .addTrustedHandlers([await reputationOracle.getAddress()]);
      });

      it("Should succeeds when aborting with not trusted address", async function () {
        //const tx = await escrow.connect(externalAddress).abort()
        //console.log(`Abort costs: ${tx.receipt.gasUsed} wei.`);
        await expect(
          escrow.connect(externalAddress).abort()
        ).to.be.revertedWith("Address calling not trusted");
      });
    });

    describe("Calling abort", function () {
      beforeEach(async () => {
        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
        await escrow
          .connect(owner)
          .addTrustedHandlers([await reputationOracle.getAddress()]);
      });

      it("Should transfer tokens to owner if contract funded when abort is called", async function () {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow.connect(owner).abort();

        const result = await token.connect(owner).balanceOf(escrow.address);
        expect(result.toString()).to.equal(
          "0",
          "Escrow has not been properly aborted"
        );
      });
    });
  });

  describe("addTrustedHandlers", async () => {
    beforeEach(async () => {
      await escrow
        .connect(owner)
        .setup(
          await reputationOracle.getAddress(),
          await recordingOracle.getAddress(),
          10,
          10,
          MOCK_URL,
          MOCK_HASH
        );
    });

    describe("Validations", function () {
      it("Should revert with the right error if caller cannot add trusted handlers", async function () {
        await expect(
          escrow
            .connect(externalAddress)
            .addTrustedHandlers([await reputationOracle.getAddress()])
        ).to.be.revertedWith("Address calling cannot add trusted handlers");
      });
    });

    describe("Add trusted handlers", async function () {
      it("Should succeeds when the contract launcher address trusted handlers and a trusted handler stores results", async () => {
        await (
          await escrow
            .connect(owner)
            .addTrustedHandlers([await reputationOracle.getAddress()])
        ).wait();

        const result: any = await (
          await escrow
            .connect(reputationOracle)
            .storeResults(MOCK_URL, MOCK_HASH)
        ).wait();

        const event = result.events[0].args;
        expect(result.events[0].event).to.equal(
          "IntermediateStorage",
          "IntermediateStorage event was not emitted"
        );
        // expect(event._url).to.equal(MOCK_URL, "Manifest url is not correct")
        // expect(event._hash).to.equal(MOCK_HASH, "Manifest hash is not correct")
      });
    });
  });

  describe("storeResults", async () => {
    describe("Validations", function () {
      it("Should revert with the right error if address calling not trusted", async function () {
        await expect(
          escrow.connect(externalAddress).storeResults(MOCK_URL, MOCK_HASH)
        ).to.be.revertedWith("Address calling not trusted");
      });

      it("Should revert with the right error if escrow not in Pending or Partial status state", async function () {
        await escrow
          .connect(owner)
          .addTrustedHandlers([await reputationOracle.getAddress()]);
        await expect(
          escrow.connect(reputationOracle).storeResults(MOCK_URL, MOCK_HASH)
        ).to.be.revertedWith("Escrow not in Pending or Partial status state");
      });
    });

    describe("Events", function () {
      beforeEach(async () => {
        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
        await escrow
          .connect(owner)
          .addTrustedHandlers([await reputationOracle.getAddress()]);
      });

      it("Should emit an event on intermediate storage", async function () {
        await expect(
          await escrow.connect(owner).storeResults(MOCK_URL, MOCK_HASH)
        )
          .to.emit(escrow, "IntermediateStorage")
          .withArgs(MOCK_URL, MOCK_HASH);
      });
    });

    describe("Store results", async function () {
      beforeEach(async () => {
        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
        await escrow
          .connect(owner)
          .addTrustedHandlers([await reputationOracle.getAddress()]);
      });

      it("Should succeeds when the contract launcher address trusted handlers and a trusted handler stores results", async () => {
        const result: any = await (
          await escrow
            .connect(reputationOracle)
            .storeResults(MOCK_URL, MOCK_HASH)
        ).wait();

        expect(result.events[0].event).to.equal(
          "IntermediateStorage",
          "IntermediateStorage event was not emitted"
        );
      });
    });
  });

  describe("setup", () => {
    describe("Validations", function () {
      it("Should revert with the right error if address calling not trusted", async function () {
        await expect(
          escrow
            .connect(externalAddress)
            .setup(
              await reputationOracle.getAddress(),
              await recordingOracle.getAddress(),
              10,
              10,
              MOCK_URL,
              MOCK_HASH
            )
        ).to.be.revertedWith("Address calling not trusted");
      });

      it("Should revert with the right error if set invalid or missing reputation oracle address", async function () {
        await expect(
          escrow
            .connect(owner)
            .setup(
              ethers.constants.AddressZero,
              await recordingOracle.getAddress(),
              10,
              10,
              MOCK_URL,
              MOCK_HASH
            )
        ).to.be.revertedWith("Invalid or missing token spender");
      });

      it("Should revert with the right error if set invalid or missing reputation oracle address", async function () {
        await expect(
          escrow
            .connect(owner)
            .setup(
              await reputationOracle.getAddress(),
              ethers.constants.AddressZero,
              10,
              10,
              MOCK_URL,
              MOCK_HASH
            )
        ).to.be.revertedWith("Invalid or missing token spender");
      });

      it("Should revert with the right error if stake out of bounds and too high", async function () {
        await expect(
          escrow
            .connect(owner)
            .setup(
              await reputationOracle.getAddress(),
              await recordingOracle.getAddress(),
              500,
              500,
              MOCK_URL,
              MOCK_HASH
            )
        ).to.be.revertedWith("Stake out of bounds");
      });
    });

    describe("Events", function () {
      it("Should emit an event on pending", async function () {
        await expect(
          escrow
            .connect(owner)
            .setup(
              await reputationOracle.getAddress(),
              await recordingOracle.getAddress(),
              10,
              10,
              MOCK_URL,
              MOCK_HASH
            )
        )
          .to.emit(escrow, "Pending")
          .withArgs(MOCK_URL, MOCK_HASH);
      });
    });

    describe("Setup escrow", async function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);
      });

      it("Should sets correct escrow with params", async () => {
        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );

        expect(await escrow.reputationOracle()).to.equal(
          await reputationOracle.getAddress()
        );
        expect(await escrow.recordingOracle()).to.equal(
          await recordingOracle.getAddress()
        );
        expect(await escrow.manifestUrl()).to.equal(MOCK_URL);
        expect(await escrow.manifestHash()).to.equal(MOCK_HASH);
        expect(await escrow.status()).to.equal(Status.Pending);
      });
    });
  });

  describe("cancel", () => {
    describe("Validations", function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );

        await escrow
          .connect(owner)
          .bulkPayOut(
            [await restAccounts[0].getAddress()],
            [100],
            MOCK_URL,
            MOCK_HASH,
            "000"
          );
      });

      it("Should revert with the right error if address calling not trusted", async function () {
        await expect(
          escrow.connect(externalAddress).cancel()
        ).to.be.revertedWith("Address calling not trusted");
      });
    });

    describe("Cancel escrow", async function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
      });

      it("Should succeeds when the contract was canceled", async () => {
        await escrow.connect(owner).cancel();
        const ststus = await escrow.status();
        expect(ststus).to.equal(Status.Cancelled);

        const balance = await token.connect(owner).balanceOf(escrow.address);
        expect(balance).to.equal("0", "Escrow has not been properly canceled");
      });
    });
  });

  describe("bulkPayOut", () => {
    describe("Validations", function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
      });

      it("Should revert with the right error if address calling is not trusted", async function () {
        const recepients = [await restAccounts[0].getAddress()];
        const amounts = [10];

        await expect(
          escrow
            .connect(externalAddress)
            .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000")
        ).to.be.revertedWith("Address calling not trusted");
      });

      it("Should revert with the right error if amount of recipients more then amount of values", async function () {
        const recepients = [
          await restAccounts[0].getAddress(),
          await restAccounts[1].getAddress(),
          await restAccounts[2].getAddress(),
        ];
        const amounts = [10, 20];

        await expect(
          escrow
            .connect(reputationOracle)
            .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000")
        ).to.be.revertedWith("Amount of recipients and values don't match");
      });

      it("Should revert with the right error if amount of recipients less then amount of values", async function () {
        const recepients = [
          await restAccounts[0].getAddress(),
          await restAccounts[1].getAddress(),
        ];
        const amounts = [10, 20, 30];

        await expect(
          escrow
            .connect(reputationOracle)
            .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000")
        ).to.be.revertedWith("Amount of recipients and values don't match");
      });

      it("Should revert with the right error if too many recipients", async function () {
        const recepients = Array.from(
          new Array(BULK_MAX_COUNT + 1),
          () => ethers.constants.AddressZero
        );
        const amounts = Array.from({ length: BULK_MAX_COUNT + 1 }, () => 1);

        await expect(
          escrow
            .connect(reputationOracle)
            .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000")
        ).to.be.revertedWith("Too many recipients");
      });
    });

    describe("Events", function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
      });

      it("Should emit an event on bulk transfer", async function () {
        const recepients = [await restAccounts[0].getAddress()];
        const amounts = [10];

        await expect(
          escrow
            .connect(owner)
            .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000")
        )
          .to.emit(escrow, "BulkTransfer")
          .withArgs(anyValue, recepients.length);
      });
    });

    describe("Bulk payout for recipients", async function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);
      });

      it("Should pays each recipient their corresponding amount", async () => {
        const account1 = await restAccounts[0].getAddress();
        const account2 = await restAccounts[1].getAddress();
        const account3 = await restAccounts[2].getAddress();

        const initialBalanceAccount1 = await token
          .connect(owner)
          .balanceOf(account1);
        const initialBalanceAccount2 = await token
          .connect(owner)
          .balanceOf(account2);
        const initialBalanceAccount3 = await token
          .connect(owner)
          .balanceOf(account3);
        const initialBalanceRecordingOracle = await token
          .connect(owner)
          .balanceOf(await recordingOracle.getAddress());
        const initialBalanceReputationOracle = await token
          .connect(owner)
          .balanceOf(await reputationOracle.getAddress());

        const recepients = [account1, account2, account3];
        const amounts = [10, 20, 30];

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );

        await escrow
          .connect(reputationOracle)
          .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000");

        const finalBalanceAccount1 = await token
          .connect(owner)
          .balanceOf(account1);
        const finalBalanceAccount2 = await token
          .connect(owner)
          .balanceOf(account2);
        const finalBalanceAccount3 = await token
          .connect(owner)
          .balanceOf(account3);
        const finalBalanceRecordingOracle = await token
          .connect(owner)
          .balanceOf(await recordingOracle.getAddress());
        const finalBalanceReputationOracle = await token
          .connect(owner)
          .balanceOf(await reputationOracle.getAddress());

        expect(
          (
            finalBalanceAccount1.toNumber() - initialBalanceAccount1.toNumber()
          ).toString()
        ).to.equal("8");
        expect(
          (
            finalBalanceAccount2.toNumber() - initialBalanceAccount2.toNumber()
          ).toString()
        ).to.equal("16");
        expect(
          (
            finalBalanceAccount3.toNumber() - initialBalanceAccount3.toNumber()
          ).toString()
        ).to.equal("24");
        expect(
          (
            finalBalanceRecordingOracle.toNumber() -
            initialBalanceRecordingOracle.toNumber()
          ).toString()
        ).to.equal("6");
        expect(
          (
            finalBalanceReputationOracle.toNumber() -
            initialBalanceReputationOracle.toNumber()
          ).toString()
        ).to.equal("6");

        expect(
          (
            finalBalanceReputationOracle.toNumber() -
            initialBalanceReputationOracle.toNumber()
          ).toString()
        ).to.equal("6");
      });

      it("Should runs from setup to bulkPayOut to complete correctly", async () => {
        const recepients = [await restAccounts[0].getAddress()];
        const amounts = [100];

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
        expect(await escrow.status()).to.equal(Status.Pending);

        await escrow
          .connect(reputationOracle)
          .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000");
        expect(await escrow.status()).to.equal(Status.Paid);

        await escrow.connect(reputationOracle).complete();
        expect(await escrow.status()).to.equal(Status.Complete);
      });

      it("Should runs from setup to bulkPayOut to complete correctly with multiple addresses", async () => {
        const recepients = [
          await restAccounts[0].getAddress(),
          await restAccounts[1].getAddress(),
          await restAccounts[2].getAddress(),
        ];
        const amounts = [10, 20, 70];

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
        expect(await escrow.status()).to.equal(Status.Pending);

        await escrow
          .connect(reputationOracle)
          .bulkPayOut(recepients, amounts, MOCK_URL, MOCK_HASH, "000");
        expect(await escrow.status()).to.equal(Status.Paid);

        await escrow.connect(reputationOracle).complete();
        expect(await escrow.status()).to.equal(Status.Complete);
      });
    });
  });

  describe("complete", () => {
    describe("Validations", function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );
      });

      it("Should revert with the right error if address calling is not trusted", async function () {
        await expect(
          escrow.connect(externalAddress).complete()
        ).to.be.revertedWith("Address calling is not trusted");
      });

      it("Should revert with the right error if escrow not in Paid status state", async function () {
        await expect(escrow.connect(owner).complete()).to.be.revertedWith(
          "Escrow not in Paid state"
        );
      });
    });

    describe("Complete escrow", async function () {
      beforeEach(async () => {
        const amount = 100;
        await token.connect(owner).transfer(escrow.address, amount);

        await escrow
          .connect(owner)
          .setup(
            await reputationOracle.getAddress(),
            await recordingOracle.getAddress(),
            10,
            10,
            MOCK_URL,
            MOCK_HASH
          );

        await escrow
          .connect(owner)
          .bulkPayOut(
            [await restAccounts[0].getAddress()],
            [100],
            MOCK_URL,
            MOCK_HASH,
            "000"
          );
      });

      it("Should succeeds when the contract launcher address trusted handlers and a trusted handler stores results", async () => {
        await escrow.connect(owner).complete();
        expect(await escrow.status()).to.equal(Status.Complete);
      });
    });
  });
});
