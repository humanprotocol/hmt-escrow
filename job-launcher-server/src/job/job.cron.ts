import { Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { Cron, CronExpression } from "@nestjs/schedule";
import Web3 from "web3";
import { CONFIRMATION_TRESHOLD, JobStatus, TransactionStatus, TransactionType } from "../common/decorators";
import { TransactionService } from "../transaction/transaction.service";
import { Web3Service } from "../web3/web3.service";
import { JobService } from "./job.service";

@Injectable()
export class JobCron {
  private web3: Web3;
  private readonly logger = new Logger(JobCron.name);

  constructor(
    private readonly jobService: JobService,
    private readonly transactionService: TransactionService,
    private readonly web3Service: Web3Service,
    private readonly configService: ConfigService,
  ) {
    this.web3 = this.web3Service.getClient(this.configService.get<string>("WEB3_CLIENT_NAME"));
  }

  @Cron(CronExpression.EVERY_10_MINUTES)
  public async createEscrow(): Promise<void> {
    this.logger.debug("Called every 30 seconds");
    const jobEntites = await this.jobService.getJobByStatus(JobStatus.PAID);

    jobEntites.map(async jobEntity => {
      if (jobEntity.transactions && Array.isArray(jobEntity.transactions) && jobEntity.transactions.length === 0)
        return;

      const transactionEntity = jobEntity.transactions[jobEntity.transactions.length - 1];

      if (transactionEntity.type !== TransactionType.ESCROW_CREATE) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} not equal ${TransactionType.ESCROW_CREATE}`,
        );
        return;
      }

      const transaction = await this.web3.eth.getTransaction(transactionEntity.hash);

      if (!transaction) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} not found by hash`,
        );
        return;
      }

      const confirmations = (await this.web3.eth.getBlockNumber()) - (transaction.blockNumber || 0);

      if (confirmations < CONFIRMATION_TRESHOLD) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} has ${confirmations} confirmations instead of ${CONFIRMATION_TRESHOLD}`,
        );
        return;
      }

      Object.assign(transactionEntity, { confirmations, status: TransactionStatus.CONFIRMED });
      await transactionEntity.save();

      this.logger.debug(
        `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} was successfully updated`,
      );

      Object.assign(jobEntity, { status: JobStatus.ESCROW_CREATED });
      await jobEntity.save();

      this.logger.debug(`Job with id ${jobEntity.id} and status ${jobEntity.status} was successfully updated`);
    });
  }

  @Cron(CronExpression.EVERY_10_MINUTES)
  public async setupEscrow(): Promise<void> {
    this.logger.debug("Called every 30 seconds");

    const jobEntites = await this.jobService.getJobByStatus(JobStatus.ESCROW_CREATED);

    jobEntites.map(async jobEntity => {
      if (jobEntity.transactions && Array.isArray(jobEntity.transactions) && jobEntity.transactions.length === 0)
        return;

      const transactionEntity = jobEntity.transactions[jobEntity.transactions.length - 1];

      if (transactionEntity.type !== TransactionType.ESCROW_SETUP) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} not equal ${TransactionType.ESCROW_CREATE}`,
        );
        return;
      }

      const transaction = await this.web3.eth.getTransaction(transactionEntity.hash);

      if (!transaction) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} not found by hash`,
        );
        return;
      }

      const confirmations = (await this.web3.eth.getBlockNumber()) - (transaction.blockNumber || 0);

      if (confirmations < CONFIRMATION_TRESHOLD) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} has ${confirmations} confirmations instead of ${CONFIRMATION_TRESHOLD}`,
        );
        return;
      }

      Object.assign(transactionEntity, { confirmations, status: TransactionStatus.CONFIRMED });
      await transactionEntity.save();

      this.logger.debug(
        `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} was successfully updated`,
      );

      const result = await this.jobService.setupEscrow(jobEntity);

      if (!result) {
        this.logger.debug(
          `Transaction with id ${transactionEntity.id} and hash ${transactionEntity.hash} and type ${transactionEntity.type} not found by hash`,
        );
        return;
      }

      Object.assign(jobEntity, { status: JobStatus.ESCROW_SETUP });
      await jobEntity.save();

      this.logger.debug(`Job with id ${jobEntity.id} and status ${jobEntity.status} was successfully updated`);
    });
  }
}
