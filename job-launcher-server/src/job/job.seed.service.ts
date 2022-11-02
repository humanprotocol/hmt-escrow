import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Repository } from "typeorm";
import { subDays } from "date-fns";
import { JobEntity } from "./job.entity";
import { generateTestJob, generateTestUser } from "../common/test";
import { UserEntity } from "../user/user.entity";


@Injectable()
export class JobSeedService {
  constructor(
    @InjectRepository(UserEntity)
    private readonly userEntityRepository: Repository<UserEntity>,
    @InjectRepository(JobEntity)
    private readonly jobEntityRepository: Repository<JobEntity>
  ) {}

  public async setup(): Promise<any> {
    const job1 = await this.jobEntityRepository.create(generateTestJob()).save();
    const job2 = await this.jobEntityRepository.create(generateTestJob()).save();


    job2.createdAt = subDays(new Date(), 7);

    await job2.save();

    
    const user1 = await this.userEntityRepository.create(generateTestUser()).save();
    const user2 = await this.userEntityRepository.create(generateTestUser()).save();

    user2.createdAt = subDays(new Date(), 7);

    await user2.save();

    return {
      users: [user1, user2],
      jobs: [job1, job2],
    };
  }

  public async tearDown(): Promise<void> {
    await this.jobEntityRepository.delete({});
  }
}
