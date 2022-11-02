import { Logger, Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { ConfigModule } from "@nestjs/config";

import { TransactionService } from "./transaction.service";
import { Web3Module } from "../web3/web3.module";
import { TransactionEntity } from "./transaction.entity";

@Module({
  imports: [TypeOrmModule.forFeature([TransactionEntity]), ConfigModule],
  providers: [Logger, TransactionService],
  exports: [TransactionService],
})
export class TransactionModule {}
