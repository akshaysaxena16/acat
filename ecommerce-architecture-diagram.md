# Cloud-native eCommerce Architecture (AWS)

This diagram matches the requested architecture: **S3 + CloudFront** for a serverless frontend and **Amazon EKS** for scalable microservices, protected by **AWS WAF**, and powered by **managed databases, messaging, and analytics**.

```mermaid
flowchart LR
  %% =========================
  %% Edge / Frontend
  %% =========================
  U[Customers\nWeb / Mobile] --> R53[Route 53 (DNS)]
  R53 --> WAF[WAF]
  WAF --> CF[CloudFront (CDN)]
  CF --> S3FE[S3 (Static Web Assets)\nHTML/CSS/JS]
  CF --> ALB

  %% =========================
  %% Networking (VPC)
  %% =========================
  subgraph VPC[VPC (Multi-AZ)]
    IGW[Internet Gateway]

    subgraph PUB[Public Subnets]
      ALB[Application Load Balancer\n(EKS Ingress)]
      NAT[NAT Gateways]
    end

    subgraph PRIV[Private Subnets]
      %% Kubernetes / Microservices
      subgraph EKS[EKS Cluster (Multi-AZ)]
        IN[Ingress Controller] --> API[API Gateway Service\n(BFF / API)]

        API --> CATALOG[Catalog Service]
        API --> SEARCH[Search Service]
        API --> CART[Cart Service]
        API --> CHECKOUT[Checkout Service]
        API --> ORDER[Order Service]
        API --> USER[User/Profile Service]
        API --> PAY[Payment Orchestrator]
        API --> NOTIF[Notification Service]
        API --> RECO[Recommendations Service]

        %% async/eventing
        ORDER --> EVT[(Event Publisher)]
        CHECKOUT --> EVT
        PAY --> EVT
      end

      %% Data Stores (Managed)
      subgraph DATA[Managed Data Stores]
        AUR[Aurora (PostgreSQL/MySQL)\nOrders / Users]:::db
        DDB[DynamoDB\nCarts / Sessions]:::db
        REDIS[ElastiCache (Redis)\nCaching / Rate Limits]:::db
        OPENSEARCH[OpenSearch\nProduct/Search Index]:::db
        S3MEDIA[S3 (Media)\nProduct Images]:::db
      end
    end
  end

  IGW --- PUB
  PRIV -->|Outbound to AWS/Public Internet| NAT
  NAT --> IGW

  CATALOG --> AUR
  USER --> AUR
  ORDER --> AUR

  CART --> DDB
  API --> REDIS
  SEARCH --> OPENSEARCH
  CATALOG --> S3MEDIA
  CF --> S3MEDIA

  %% =========================
  %% Messaging / Integration
  %% =========================
  subgraph MSG[Messaging / Integration]
    SNS[SNS (Topics)]
    SQS[SQS (Queues)]
    DLQ[DLQ]
  end

  EVT --> SNS
  SNS --> SQS
  SQS --> NOTIF
  SQS --> RECO
  SQS --> ORDER
  SQS --> DLQ

  %% =========================
  %% Identity / Secrets
  %% =========================
  subgraph SEC[Security]
    COG[Cognito\nAuthN/AuthZ]
    SECRETS[Secrets Manager]
    KMS[KMS]
  end

  U --> COG
  API --> COG
  API --> SECRETS
  SECRETS --> KMS

  %% =========================
  %% Observability
  %% =========================
  subgraph OBS[Observability]
    CW[CloudWatch Logs/Metrics]
    XR[X-Ray / Tracing]
  end

  CF --> CW
  ALB --> CW
  EKS --> CW
  EKS --> XR

  %% =========================
  %% Analytics
  %% =========================
  subgraph ANA[Analytics]
    KDS[Kinesis Data Streams / Firehose]
    DLAKE[S3 Data Lake]
    GLUE[Glue Catalog/ETL]
    ATH[Athena]
    QS[QuickSight]
  end

  CF --> KDS
  API --> KDS
  KDS --> DLAKE
  DLAKE --> GLUE
  GLUE --> ATH
  ATH --> QS

  classDef db fill:#eef7ff,stroke:#2b6cb0,stroke-width:1px
```

## Notes (why this fits your description)

- **Serverless frontend**: CloudFront caches and serves the SPA from **S3**; media assets can also be served from S3 via CloudFront.
- **Secure edge**: **WAF** protects CloudFront (and therefore both static and dynamic paths).
- **Scalable backend**: CloudFront routes API calls to an **ALB** in front of **EKS**, where microservices scale horizontally.
- **Managed backbone**: Aurora/DynamoDB/Redis/OpenSearch for data, SNS/SQS for async workflows, and a Kinesis→S3→Athena/QuickSight pipeline for analytics.

## Disaster Recovery (DR) strategy (Multi-Region)

The following DR view shows a typical **warm-standby / active-passive** design: a secondary AWS region is kept ready with scaled-down capacity and continuously replicated data, then promoted during a regional outage.

```mermaid
flowchart LR
  U[Customers\nWeb / Mobile] --> R53[Route 53\nFailover / Latency Routing\n+ Health Checks]
  R53 --> CF[CloudFront (Global)]
  CF --> WAF[WAF (Global)]

  %% -------------------------
  %% Primary region (Region A)
  %% -------------------------
  subgraph A[Region A (Primary)]
    A_S3FE[S3 (Frontend)]

    subgraph A_VPC[VPC (Multi-AZ)]
      A_IGW[Internet Gateway]

      subgraph A_PUB[Public Subnets]
        A_ALB[ALB (Ingress)]
        A_NAT[NAT Gateways]
      end

      subgraph A_PRIV[Private Subnets]
        A_EKS[EKS Microservices]

        subgraph A_DATA[Region A Data]
          A_AUR[(Aurora Primary Writer)]
          A_DDB[(DynamoDB Global Tables)]
          A_OS[(OpenSearch Domain)]
          A_REDIS[(ElastiCache Redis)]
          A_S3DATA[(S3 Data Lake / Backups)]
        end
      end

      A_IGW --- A_PUB
      A_PRIV -->|Outbound| A_NAT
      A_NAT --> A_IGW
    end

    A_ALB --> A_EKS
    A_EKS --> A_AUR
    A_EKS --> A_DDB
    A_EKS --> A_OS
    A_EKS --> A_REDIS
    A_EKS --> A_S3DATA
  end

  %% -------------------------
  %% DR region (Region B)
  %% -------------------------
  subgraph B[Region B (DR / Warm Standby)]
    B_S3FE[S3 (Frontend Replica)]

    subgraph B_VPC[VPC (Multi-AZ)]
      B_IGW[Internet Gateway]

      subgraph B_PUB[Public Subnets]
        B_ALB[ALB (Ingress)]
        B_NAT[NAT Gateways]
      end

      subgraph B_PRIV[Private Subnets]
        B_EKS[EKS Microservices\n(Scaled down / Ready)]

        subgraph B_DATA[Region B Data]
          B_AUR[(Aurora Global DB\nSecondary / Reader)]
          B_DDB[(DynamoDB Global Tables)]
          B_OS[(OpenSearch\nRestore / CCR)]
          B_REDIS[(ElastiCache\nRestore from backups)]
          B_S3DATA[(S3 Replica\n(Data Lake / Backups))]
        end
      end

      B_IGW --- B_PUB
      B_PRIV -->|Outbound| B_NAT
      B_NAT --> B_IGW
    end

    B_ALB --> B_EKS
    B_EKS --> B_AUR
    B_EKS --> B_DDB
    B_EKS --> B_OS
    B_EKS --> B_REDIS
    B_EKS --> B_S3DATA
  end

  %% -------------------------
  %% CloudFront origin failover
  %% -------------------------
  CF -->|Origin: static| A_S3FE
  CF -->|Origin: static failover| B_S3FE
  CF -->|Origin: APIs| A_ALB
  CF -->|Origin: API failover| B_ALB

  %% -------------------------
  %% Replication / backups
  %% -------------------------
  A_S3FE -. CRR .-> B_S3FE
  A_S3DATA -. CRR .-> B_S3DATA
  A_AUR == Aurora Global Database Replication ==> B_AUR
  A_DDB == DynamoDB Global Tables Replication ==> B_DDB
  A_OS -. Snapshots/CCR .-> B_OS
  A_REDIS -. Backups .-> B_REDIS

  %% -------------------------
  %% DR actions (promotion)
  %% -------------------------
  B_AUR -->|Promote to writer\non failover| B_AUR
```

### DR operational notes (what happens during a regional outage)

- **Traffic failover**: Route 53 health checks fail over to Region B (and/or CloudFront origin failover routes API/static origins to Region B).
- **Datastore promotion**:
  - **Aurora**: promote the Region B cluster to writer (Aurora Global Database).
  - **DynamoDB**: Global Tables continue serving reads/writes in Region B.
  - **OpenSearch / Redis**: restore from snapshots/backups (or use cross-cluster replication where applicable).
- **EKS recovery**: Region B EKS runs the same workloads (typically via GitOps/CI) at reduced scale until failover; scale up on incident.
