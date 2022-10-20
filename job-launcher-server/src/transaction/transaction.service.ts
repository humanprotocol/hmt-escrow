import { Injectable, Logger, NotFoundException } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { ConfigService } from "@nestjs/config";
import { FindConditions, FindManyOptions, FindOneOptions, Repository } from "typeorm";

import { TransactionEntity } from "./transaction.entity";
import { TransactionStatus } from "../common/decorators";
import { Web3Service } from "../web3/web3.service";
import Web3 from "web3";
import { ITransactionCreateDto } from "./interfaces";

@Injectable()
export class TransactionService {
  private web3: Web3;
  private readonly logger = new Logger(TransactionService.name);

  constructor(
    @InjectRepository(TransactionEntity)
    private readonly transactionEntityRepository: Repository<TransactionEntity>,
    private readonly web3Service: Web3Service,
    private readonly configService: ConfigService,
  ) {
    this.web3 = this.web3Service.getClient(this.configService.get<string>("WEB3_CLIENT_NAME"));
  }

  public async getTransactionById(transactionId: number): Promise<TransactionEntity> {
    const transactionEntity = await this.findOne({ id: transactionId });

    if (!transactionEntity) throw new NotFoundException("Transaction not found");

    return transactionEntity;
  }

  public async getTransactionByStatus(status: TransactionStatus): Promise<TransactionEntity[]> {
    const results = await this.find({ status });

    if (results && results.length === 0) throw new NotFoundException(`Transactions with status ${status} not found`);

    return results;
  }

  public async create(dto: ITransactionCreateDto, jobId: number): Promise<TransactionEntity> {
    // TODO: Change status based on amout of confirmations
    const transactionEntity = await this.transactionEntityRepository
      .create({
        ...dto,
        jobId
      })
      .save();

    return transactionEntity;
  }

  public findOne(
    where: FindConditions<TransactionEntity>,
    options?: FindOneOptions<TransactionEntity>,
  ): Promise<TransactionEntity | undefined> {
    return this.transactionEntityRepository.findOne({ where, ...options });
  }

  public find(
    where: FindConditions<TransactionEntity>,
    options?: FindManyOptions<TransactionEntity>,
  ): Promise<TransactionEntity[]> {
    return this.transactionEntityRepository.find({
      where,
      order: {
        createdAt: "DESC",
      },
      ...options,
    });
  }
}
