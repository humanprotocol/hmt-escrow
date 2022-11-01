import { Test } from "@nestjs/testing";
import { Logger } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { TypeOrmModule } from "@nestjs/typeorm";
import { v4 } from "uuid";

import { generateUserCreateDto } from "../common/test";
import { DatabaseModule } from "../database/database.module";
import { PostmarkModule } from "../postmark/postmark.module";
import { UserService } from "./user.service";
import { UserSeedModule } from "./user.seed.module";
import { UserSeedService } from "./user.seed.service";
import { UserEntity } from "./user.entity";
import { UserStatus } from "../common/decorators";
import { AuthEntity } from "../auth/auth.entity";

describe("UserService", () => {
  let userService: UserService;
  let userSeedService: UserSeedService;

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          envFilePath: `.env.${process.env.NODE_ENV as string}`,
        }),
        DatabaseModule,
        PostmarkModule,
        TypeOrmModule.forFeature([UserEntity]),
        TypeOrmModule.forFeature([AuthEntity]),
        UserSeedModule,
      ],
      providers: [Logger, UserService, UserSeedService],
    }).compile();

    userService = moduleRef.get<UserService>(UserService);
    userSeedService = moduleRef.get<UserSeedService>(UserSeedService);
  });

  afterEach(async () => {
    await userSeedService.tearDown();
  });

  describe("createPasswordHash", () => {
    it("should generate password hash", () => {
      const hash = userService.createPasswordHash("human");
      expect(hash).toEqual("79a5478768d2447431a90f7f4549df735f50ad541371464c248abc7522dc3a01");
    });
  });

  describe("create", () => {
    it("create user (ConflictException lowercase)", async () => {
      const entities = await userSeedService.setup();
      return userService
        .create(generateUserCreateDto({ email: entities.users[0].email }))
        .then(() => fail(new Error()))
        .catch(e => {
          expect(e.status).toEqual(409);
        });
    });

    it("create user (ConflictException uppercase)", async () => {
      const entities = await userSeedService.setup();
      return userService
        .create(generateUserCreateDto({ email: entities.users[0].email }))
        .then(() => fail(new Error()))
        .catch(e => {
          expect(e.status).toEqual(409);
        });
    });

    it("create user", () => {
      return userService.create(generateUserCreateDto());
    });
  });

  describe("update", () => {
    it("should update email", async () => {
      const entities = await userSeedService.setup();
      const email = `trejgun+${v4()}@gmail.com`;
      const userEntity = await userService.update({ id: entities.users[0].id }, { email });
      expect(userEntity.email).toEqual(email);
      expect(userEntity.status).toEqual(UserStatus.PENDING);
    });

    it("should NOT update email", async () => {
      const entities = await userSeedService.setup();
      const userEntity = await userService.update(
        { id: entities.users[0].id },
        { email: entities.users[0].email },
      );
      expect(userEntity.email).toEqual(entities.users[0].email);
      expect(userEntity.status).toEqual(UserStatus.ACTIVE);
    });
  });
});
