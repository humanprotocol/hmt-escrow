import { Module } from "@nestjs/common";
import { APP_GUARD, APP_PIPE } from "@nestjs/core";
import { ConfigModule } from "@nestjs/config";
import { ScheduleModule } from "@nestjs/schedule";

import { AppController } from "./app.controller";
import { AuthModule } from "./auth/auth.module";
import { DatabaseModule } from "./database/database.module";
import { JwtHttpGuard, RolesGuard } from "./common/guards";
import { UserModule } from "./user/user.module";
import { HttpValidationPipe } from "./common/pipes";
import { NetworkModule } from "./network/network.module";
import { JobModule } from "./job/job.module";
import { Web3Module } from "./web3/web3.module";
import { HealthModule } from "./health/health.module";

@Module({
  providers: [
    {
      provide: APP_GUARD,
      useClass: JwtHttpGuard,
    },
    {
      provide: APP_GUARD,
      useClass: RolesGuard,
    },
    {
      provide: APP_PIPE,
      useClass: HttpValidationPipe,
    },
  ],
  imports: [
    ScheduleModule.forRoot(),
    ConfigModule.forRoot({
      envFilePath: `.env.${process.env.NODE_ENV as string}`,
    }),
    Web3Module.forRoot({
      name: process.env.WEB3_CLIENT_NAME as string,
      url: process.env.WEB3_PROVIDER_URL as string,
    }),
    AuthModule,
    DatabaseModule,
    HealthModule,
    UserModule,
    JobModule,
    NetworkModule,
  ],
  controllers: [AppController],
})
export class AppModule {}
