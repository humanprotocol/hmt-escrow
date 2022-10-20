import { Logger, Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { ConfigModule } from "@nestjs/config";

import { PostmarkModule } from "../postmark/postmark.module";
import { JobService } from "./job.service";
import { JobEntity } from "./job.entity";
import { JobController } from "./job.controller";
import { NetworkModule } from "../network/network.module";
import { Web3Module } from "../web3/web3.module";
import { JobCron } from "./job.cron";
import { StorageModule } from "../storage/storage.module";
import { TransactionModule } from "../transaction/transaction.module";
import { HttpModule } from "@nestjs/axios";

@Module({
  imports: [
    TypeOrmModule.forFeature([JobEntity]),
    TransactionModule,
    NetworkModule,
    Web3Module,
    ConfigModule,
    StorageModule,
    PostmarkModule,
    HttpModule,
  ],
  controllers: [JobController],
  providers: [Logger, JobService, JobCron],
  exports: [JobService],
})
export class JobModule {}
