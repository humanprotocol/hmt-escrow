import { Test } from "@nestjs/testing";
import { Logger, Provider } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { TypeOrmModule } from "@nestjs/typeorm";

import { generateJobCreateDto } from "../common/test";
import { DatabaseModule } from "../database/database.module";
import { PostmarkModule } from "../postmark/postmark.module";
import { JobService } from "./job.service";
import { JobSeedModule } from "./job.seed.module";
import { JobSeedService } from "./job.seed.service";
import { JobEntity } from "./job.entity";
import { JobStatus, UserStatus } from "../common/decorators";
import { AuthEntity } from "../auth/auth.entity";
import { UserEntity } from "../user/user.entity";
import { UserSeedService } from "../user/user.seed.service";
import { UserService } from "../user/user.service";
import { UserSeedModule } from "../user/user.seed.module";
import { TransactionService } from "../transaction/transaction.service";
import { NetworkService } from "../network/network.service";
import { StorageService } from "../storage/storage.service";
import { Web3Service } from "../web3/web3.service";
import { HttpService } from "@nestjs/axios";
import { TransactionEntity } from "../transaction/transaction.entity";
import { S3 } from "aws-sdk";
import { s3Provider } from "../common/providers";
import { WEB3_CLIENT } from "../web3/web3.constants";

describe("JobService", () => {
  let jobService: JobService;
  let jobSeedService: JobSeedService;

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          envFilePath: `.env.${process.env.NODE_ENV as string}`,
        }),
        DatabaseModule,
        PostmarkModule,
        TypeOrmModule.forFeature([UserEntity]),
        TypeOrmModule.forFeature([JobEntity]),
        TypeOrmModule.forFeature([AuthEntity]),
        TypeOrmModule.forFeature([TransactionEntity]),
        JobSeedModule,
        UserSeedModule
      ],
      providers: [Logger, UserService, UserSeedService, JobService, JobSeedService, TransactionService, NetworkService, StorageService, Web3Service, HttpService, s3Provider],
    }).compile();

    jobService = moduleRef.get<JobService>(JobService);
    jobSeedService = moduleRef.get<JobSeedService>(JobSeedService);
  });
  

  afterEach(async () => {
   // await jobSeedService.tearDown();
  });

  describe("create", () => {
    it("create job (ConflictException bucket does not to have right permissions)", async () => {
      const entities = await jobSeedService.setup();
      return jobService
        .create(generateJobCreateDto(), entities.users[0].id)
        .then(() => fail(new Error()))
        .catch(e => {
          expect(e.status).toEqual(409);
        });
    });

    /*

    it("create job (ConflictException uppercase)", async () => {
      const entities = await jobSeedService.setup();
      return jobService
        .create(generateJobCreateDto({ email: entities.jobs[0].email }))
        .then(() => fail(new Error()))
        .catch(e => {
          expect(e.status).toEqual(409);
        });
    });
    
    */
    it("create job", async () => {
      const entities = await jobSeedService.setup();
      const job = await jobService.create(generateJobCreateDto(), entities.users[0].id);
      expect(job.status).toEqual(JobStatus.PENDING);
    });
  });

  /* describe("update", () => {
    it("should update email", async () => {
      const entities = await jobSeedService.setup();
      const email = `trejgun+${v4()}@gmail.com`;
      const jobEntity = await jobService.update({ id: entities.jobs[0].id }, { email });
      expect(jobEntity.email).toEqual(email);
      expect(jobEntity.status).toEqual(JobStatus.PENDING);
    });

    it("should NOT update email", async () => {
      const entities = await jobSeedService.setup();
      const jobEntity = await jobService.update(
        { id: entities.jobs[0].id },
        { email: entities.jobs[0].email },
      );
      expect(jobEntity.email).toEqual(entities.jobs[0].email);
      expect(jobEntity.status).toEqual(JobStatus.LAUNCHED);
    });
  }); */
});
