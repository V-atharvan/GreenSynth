# DOE REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/doe/preview` | `POST` | Calculate run count preview and workload warnings |
| `/api/v1/doe` | `POST` | Create DOE study and generate design matrix |
| `/api/v1/doe` | `GET` | List project DOE studies |
| `/api/v1/doe/{id}` | `GET` | Get DOE study details |
| `/api/v1/doe/{id}/approve` | `POST` | Approve study and lock version V1 |
| `/api/v1/doe/{id}/regenerate` | `POST` | Create version V2 and regenerate design matrix |
| `/api/v1/doe/{id}/proposed-experiments` | `GET` | List proposed experiment runs |
| `/api/v1/doe/proposed-experiments/{id}/convert` | `POST` | Convert run to PLANNED laboratory experiment |
| `/api/v1/doe/{id}/analysis` | `GET` | Compute statistical main effects & response surface fit |
| `/api/v1/doe/{id}/export` | `GET` | Export CSV design matrix |
