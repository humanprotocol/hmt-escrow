import { Controller, Get, HttpCode, Param } from "@nestjs/common";
import { ApiBearerAuth, ApiTags } from "@nestjs/swagger";
import { INetworkDto } from "./interfaces";
import { NetworkService } from "./network.service";

@ApiBearerAuth()
@ApiTags("Network")
@Controller("/network")
export class NetworkController {
  constructor(private readonly networkService: NetworkService) {}

  @Get("/")
  @HttpCode(200)
  public getList(): INetworkDto[] {
    return this.networkService.getList();
  }

  @Get("/:id")
  @HttpCode(200)
  public getById(@Param("id") id: string): INetworkDto {
    return this.networkService.getNetworkById(id);
  }
}
