import { Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";

import { JobSeedService } from "./job.seed.service";
import { JobEntity } from "./job.entity";
import { UserEntity } from "../user/user.entity";
import { TransactionEntity } from "../transaction/transaction.entity";

@Module({
  imports: [
    TypeOrmModule.forFeature([JobEntity, UserEntity, TransactionEntity]),
  ],
  providers: [JobSeedService],
  exports: [JobSeedService],
})
export class JobSeedModule {}
