import { BadGatewayException, Injectable, Logger, NotFoundException } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { ConfigService } from "@nestjs/config";
import { FindConditions, FindManyOptions, FindOneOptions, Repository } from "typeorm";
import * as crypto from "crypto";
import EscrowAbi from '../contracts/EscrowAbi.json';
import EscrowFactoryAbi from "../contracts/EscrowFactoryAbi.json";

import { JobEntity } from "./job.entity";
import { CONFIRMATION_TRESHOLD, JobMode, JobRequestType, JobStatus, TransactionStatus, TransactionType } from "../common/decorators";
import { IJobCreateDto } from "./interfaces";
import { NetworkService } from "../network/network.service";
import { Web3Service } from "../web3/web3.service";
import Web3 from "web3";
import { StorageService } from "../storage/storage.service";
import { IJobDto, IManifestDataItemDto, IManifestDto, jobFormatter, manifestFormatter } from "./serializers/job.responses";
import { firstValueFrom } from "rxjs";
import { HttpService } from "@nestjs/axios";
import { IJobManifestDto } from "./interfaces/manifest";
import { TransactionService } from "../transaction/transaction.service";
import { SortDirection } from "../common/collection";
import { DATA_SAMPLE_SIZE } from "../common/constants";
import { avg, isAnGroundTruthDataAnnotations, isAnGroundTruthDataImage, max, min } from "../common/helpers";
import { IJobFeeRangeDto } from "./interfaces/feeRange";
import { NetworkId } from "../common/constants/networks";

@Injectable()
export class JobService {
  private web3: Web3;
  private readonly logger = new Logger(JobService.name);
  private recordingOracleUrl: string;
  private reputationOracleUrl: string;
  private exchangeOracleUrl: string;
  private recordingOracleStake: number;
  private reputationOracleStake: number;
  private recordingOracleAddress: string;
  private reputationOracleAddress: string;
  private exchangeOracleAddress: string;

  constructor(
    @InjectRepository(JobEntity)
    private readonly jobEntityRepository: Repository<JobEntity>,
    private readonly tansactionService: TransactionService,
    private readonly networkService: NetworkService,
    private readonly storageService: StorageService,
    private readonly web3Service: Web3Service,
    private readonly configService: ConfigService,
    private readonly httpService: HttpService,
  ) {
    this.web3 = this.web3Service.getClient(this.configService.get<string>("WEB3_CLIENT_NAME", ""));
    this.recordingOracleAddress = this.configService.get<string>(
      "RECORDING_ORACLE_ADDRESS", ""
    );
    this.reputationOracleAddress = this.configService.get<string>(
      "REPUTATION_ORACLE_ADDRESS", ""
    );
    this.exchangeOracleAddress = this.configService.get<string>(
      "EXCHANGE_ORACLE_ADDRESS", ""
    );
    this.recordingOracleUrl = this.configService.get<string>("RECORDING_ORACLE_URL", "");
    this.reputationOracleUrl = this.configService.get<string>("REPUTATION_ORACLE_URL", "");
    this.exchangeOracleUrl = this.configService.get<string>("EXCHANGE_ORACLE_URL", "");
    this.recordingOracleStake = this.configService.get<number>("RECORDING_ORACLE_STAKE", 0);
    this.reputationOracleStake = this.configService.get<number>("REPUTATION_ORACLE_STAKE", 0);
  }

  public async getJobByUser(userId: number): Promise<JobEntity[]> {
    return this.jobEntityRepository.find({
      where: {
        userId
      },
      order: {
        createdAt: SortDirection.ASC,
      },
      relations: ["transactions"],
    });
  }

  public async getJobById(jobId: number): Promise<IJobDto> {
    const jobEntity = await this.findOne({ id: jobId });

    if (!jobEntity) throw new NotFoundException("Job not found");

    return jobFormatter(jobEntity);
  }

  public async getJobByStatus(status: JobStatus): Promise<JobEntity[]> {
    const results = await this.jobEntityRepository.find({
      where: {
        status
      },
      order: {
        createdAt: SortDirection.ASC,
      },
      relations: ["transactions"],
    });

    if (results && results.length === 0) throw new NotFoundException(`Jobs with status ${status} not found`);

    return results;
  }

  public async getFeeRange(): Promise<IJobFeeRangeDto> {
    const jobEntities = await this.jobEntityRepository.find({
      where: {
        status: JobStatus.PAID
      }
    });

    const fees = jobEntities.map((jobEntity: JobEntity) => {
      return jobEntity.fee
    })

    return {
      min: min(fees) || 0,
      avg: avg(fees) || 0,
      max: max(fees) || 0
    }
  }

  public async approve(jobId: number): Promise<boolean> {
    const jobEntity = await this.findOne({ id: jobId });

    if (!jobEntity) throw new NotFoundException("Job not found");

    const jobLauncherUrl = this.configService.get<string>("JOB_LAUNCHER_URL");

    const exchangeOracleUrl = this.configService.get<string>("EXCHANGE_ORACLE_URL");

    const result = await firstValueFrom(
      this.httpService.post(`${exchangeOracleUrl}/job`, {
        manifest_url: `${jobLauncherUrl}/job/manifest/${jobId}`,
        escrow_address: jobEntity.escrowAddress,
        network: jobEntity.networkId
      }),
    );
    if (!result) return false;
    
    Object.assign(jobEntity, { status: JobStatus.LAUNCHED });
    jobEntity.save();

    return true;
  }

  public async create(dto: IJobCreateDto, userId: number): Promise<IJobDto> {
    const { dataUrl, groundTruthFileUrl, fee } = dto;

    const networkId = NetworkId.LOCAL_GANACHE;

    if (!await this.storageService.isBucketValid(dataUrl)) {
      throw new BadGatewayException("Bucket does not to have right permissions");
    }

    if (groundTruthFileUrl) {
      if (!await this.storageService.isFileValid(groundTruthFileUrl)) {
        this.logger.debug("File does not to have right permissions")
        // throw new BadGatewayException("File does not to have right permissions");
      }

      const groundTruthData = await this.storageService.getFileFromUrl(groundTruthFileUrl);

      if (!await this.isGroundTruthDataValid(groundTruthData)) {
        this.logger.debug("Ground truth data is not valid")
        // throw new BadGatewayException("Ground truth data is not valid");
      }
    }
    
    const data = await this.storageService.getDataFromBucket(dataUrl);
    
    const transaction = await this.web3.eth.getTransaction(dto.transactionHash);
    //if (!transaction) throw new NotFoundException("Transaction not found by hash");

    // TODO: Return in time
    /* 
    const confirmations = await this.web3.eth.getBlockNumber() - (transaction.blockNumber || 0)

    if (confirmations < CONFIRMATION_TRESHOLD) {
      this.logger.error(`Transaction has ${confirmations} confirmations instead of ${CONFIRMATION_TRESHOLD}`)
      throw new NotFoundException("Transaction has not enough amount of confirmations");
    } 
    */

    const manifest: IJobManifestDto = {
      data: JSON.stringify(data),
      dataUrl,
      datasetLength: data.length,
      recordingOracleAddress: this.recordingOracleAddress,
      reputationOracleAddress: this.reputationOracleAddress,
      exchangeOracleAddress: this.exchangeOracleAddress,
      recordingOracleUrl: this.recordingOracleUrl,
      reputationOracleUrl: this.reputationOracleUrl,
      exchangeOracleUrl: this.exchangeOracleUrl,
      recordingOracleStake: this.recordingOracleStake,
      reputationOracleStake: this.reputationOracleStake,
      annotationsPerImage: dto.annotationsPerImage,
      labels: dto.labels,
      requesterDescription: dto.requesterDescription,
      requesterAccuracyTarget: dto.requesterAccuracyTarget,
      price: dto.price,
      mode: JobMode.BATCH,
      requestType: JobRequestType.IMAGE_LABEL_BINARY,
    };

    const manifestHash = crypto.createHash("sha256").update(manifest.toString()).digest("hex");

    const jobEntity = await this.jobEntityRepository
      .create({
        ...manifest,
        fee,
        networkId,
        userId,
        manifestHash,
        tokenAddress: this.web3Service.tokenAddress,
        status: JobStatus.PAID,
      })
      .save();

    if (!jobEntity) throw new NotFoundException("Job was not created");

    await this.tansactionService.create(
      {
        amount: Number(Web3.utils.fromWei('100000', "ether")),//transaction.value, "ether")),
        hash: 'asdsad',//transaction.hash,
        type: TransactionType.TOPUP,
        status: TransactionStatus.CONFIRMED
      },
      jobEntity.id,
    );
    
    const escrowAddress = await this.createEscrow(jobEntity);
    Object.assign(jobEntity, { escrowAddress: this.web3.utils.toChecksumAddress(escrowAddress) })
    await jobEntity.save();

    this.approve(jobEntity.id)

    return jobFormatter(jobEntity);
  }

  public async createEscrow(jobEntity: JobEntity): Promise<string> {
    const escrowFactoryContract = new this.web3.eth.Contract(
      EscrowFactoryAbi as any,
      this.configService.get<string>("WEB3_ESCROW_FACTORY_ADDRESS"),
    );

    const jobLauncherAddress = this.configService.get<string>("WEB3_JOB_LAUNCHER_ADDRESS", "");
    const escrowAddress = await escrowFactoryContract.methods
      .createEscrow([
        this.web3.utils.toChecksumAddress(jobEntity.reputationOracleAddress),
        this.web3.utils.toChecksumAddress(jobEntity.recordingOracleAddress)
      ])
      .call({ 
        from: this.web3.utils.toChecksumAddress(jobLauncherAddress)
      })


    this.logger.debug("Escrow Address: ", escrowAddress);
    
    return escrowAddress;
  }

  public async setupEscrow(jobEntity: JobEntity): Promise<string> {
    if (!jobEntity.escrowAddress) {
      this.logger.debug(`Escrow address does not exists for job with id ${jobEntity.id}`);
      throw new NotFoundException("Escrow address does not exists");
    }

    const escrowContract = new this.web3.eth.Contract(
      EscrowAbi as any,
      jobEntity.escrowAddress,
    );

    const jobLauncherAddress = this.configService.get<string>("WEB3_JOB_LAUNCHER_ADDRESS", "");
    const jobLauncherUrl = this.configService.get<string>("JOB_LAUNCHER_URL", "");
    const manifestUrl = `${jobLauncherUrl}/job/${jobEntity.id}/manifest`

    const result = await escrowContract.methods
      .setup(
        this.web3.utils.toChecksumAddress(jobEntity.reputationOracleAddress),
        this.web3.utils.toChecksumAddress(jobEntity.recordingOracleAddress),
        jobEntity.reputationOracleStake,
        jobEntity.recordingOracleStake,
        manifestUrl,
        jobEntity.manifestHash
      )
      .send({ from: this.web3.utils.toChecksumAddress(jobLauncherAddress) }, async (error: any, transactionHash: any) => {
        if (error) {
          this.logger.debug(`Escrow was not setup for job with id ${jobEntity.id}`);
          throw new NotFoundException("Escrow was not setup");
        }

        if (!transactionHash) throw new NotFoundException("Transaction hash didn't receive");

        await this.tansactionService.create(
          {
            amount: 0,
            hash: transactionHash,
            type: TransactionType.ESCROW_SETUP,
            status: TransactionStatus.PENDING
          },
          jobEntity.id,
        );
      })

    this.logger.debug("Escrow address was setup with result: ", result);
    return result;
  }

  public findOne(
    where: FindConditions<JobEntity>,
    options?: FindOneOptions<JobEntity>,
  ): Promise<JobEntity | undefined> {
    return this.jobEntityRepository.findOne({ where, ...options });
  }

  public find(where: FindConditions<JobEntity>, options?: FindManyOptions<JobEntity>): Promise<JobEntity[]> {
    return this.jobEntityRepository.find({
      where,
      order: {
        createdAt: SortDirection.DESC,
      },
      ...options,
    });
  }

  public async getManifest(jobId: number): Promise<IManifestDto> {
    const jobEntity = await this.findOne({ id: jobId });

    if (!jobEntity) throw new NotFoundException("Job not found");

    return manifestFormatter(jobEntity);
  }

  public async getDataSample(jobId: number): Promise<IManifestDataItemDto[]> {
    const jobEntity = await this.findOne({ id: jobId });

    if (!jobEntity) throw new NotFoundException("Job not found");

    const data = JSON.parse(jobEntity.data)

    return this.getRandomSample(data, DATA_SAMPLE_SIZE);
  }

  private getRandomSample(data: IManifestDataItemDto[], n: number): IManifestDataItemDto[] {
    const length = data == null ? 0 : data.length
    if (!length || n < 1) {
        return []
        }
        n = n > length ? length : n

        let index = -1
        const result = data.slice()
        
        while (++index < n) {
            const rand = index + Math.floor(Math.random() * (length - index ))
            
            const value = result[rand]
            result[rand] = result[index]
            result[index] = value
        }

        return result.slice(0,n)
  }

  private isGroundTruthDataValid(groundTruthData: any) {
    if (Array.isArray(groundTruthData.images) && groundTruthData.images.length === 0) {
      this.logger.debug("Images array is empty")
      // throw new NotFoundException("Images array is empty");
      return false
    }

    if (Array.isArray(groundTruthData.annotations) && groundTruthData.annotations.length === 0) {
      this.logger.debug("Anotations array is empty")
      // throw new NotFoundException("Anotations array is empty");
      return false
    }

    if (groundTruthData.images.length !== groundTruthData.annotations.length) {
      this.logger.debug("Images and Anotations has different size")
      // throw new NotFoundException("Images and Anotations has different size");
      return false
    }

    groundTruthData.images.forEach((image: any, index: number) => {
      if (!isAnGroundTruthDataImage(image)) {
        this.logger.debug(`Object with index ${index} has incorrect implementation`)
        // throw new NotFoundException(`Object with index ${index} has incorrect implementation`);
      }
    })

    groundTruthData.annotations.forEach((annotation: any, index: number) => { 
      if (isAnGroundTruthDataAnnotations(annotation)) {
        this.logger.debug(`Object with index ${index} has incorrect implementation`)
        // throw new NotFoundException(`Object with index ${index} has incorrect implementation`);
      }
    })

    return true;
  }
}
