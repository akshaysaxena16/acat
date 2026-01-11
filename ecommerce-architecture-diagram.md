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
  CF --> ALB[Application Load Balancer\nEKS Ingress]

  %% =========================
  %% Kubernetes / Microservices
  %% =========================
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

  ALB --> IN

  %% =========================
  %% Data Stores (Managed)
  %% =========================
  subgraph DATA[Managed Data Stores]
    AUR[Aurora (PostgreSQL/MySQL)\nOrders / Users]:::db
    DDB[DynamoDB\nCarts / Sessions]:::db
    REDIS[ElastiCache (Redis)\nCaching / Rate Limits]:::db
    OPENSEARCH[OpenSearch\nProduct/Search Index]:::db
    S3MEDIA[S3 (Media)\nProduct Images]:::db
  end

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
