import { Logger, Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";

import { postmarkProvider } from "../common/providers/postmark";
import { PostmarkService } from "./postmark.service";

@Module({
  imports: [ConfigModule],
  providers: [postmarkProvider, Logger, PostmarkService],
  exports: [PostmarkService],
})
export class PostmarkModule {}
