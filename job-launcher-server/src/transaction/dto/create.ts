import { ApiProperty } from "@nestjs/swagger";
import { IsEnum, IsNumber, IsPositive, IsString } from "class-validator";
import { TransactionStatus, TransactionType } from "../../common/decorators";
import { ITransactionCreateDto } from "../interfaces";

export class TransactionCreateDto implements ITransactionCreateDto {
  @ApiProperty()
  @IsNumber()
  @IsPositive()
  public amount: number;

  @ApiProperty()
  @IsString()
  public hash: string;

  @ApiProperty()
  @IsEnum(TransactionType)
  public type: TransactionType;

  @ApiProperty()
  @IsEnum(TransactionStatus)
  status: TransactionStatus;
}
