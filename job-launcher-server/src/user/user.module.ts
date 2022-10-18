import { Logger, Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { ConfigModule } from "@nestjs/config";

import { PostmarkModule } from "../postmark/postmark.module";
import { UserService } from "./user.service";
import { UserEntity } from "./user.entity";
import { UserController } from "./user.controller";
import { AuthEntity } from "../auth/auth.entity";

@Module({
  imports: [TypeOrmModule.forFeature([UserEntity, AuthEntity]), ConfigModule, PostmarkModule],
  controllers: [UserController],
  providers: [Logger, UserService],
  exports: [UserService],
})
export class UserModule {}
