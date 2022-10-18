import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";

import { NetworkService } from "./network.service";
import { NetworkController } from "./network.controller";

@Module({
  imports: [ConfigModule],
  controllers: [NetworkController],
  providers: [NetworkService],
  exports: [NetworkService],
})
export class NetworkModule {}
