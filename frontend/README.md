# RFP Ignite Frontend

React + TypeScript + Tailwind CSS frontend for the RFP Ignite Agentic AI pipeline.

## Prerequisites

- Node.js 18+ and npm
- Backend API running at `http://localhost:8000` (run `python api.py` from the project root)

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. (Optional) Configure API base URL:
Create a `.env` file in the `frontend/` directory:
```
VITE_API_BASE_URL=http://localhost:8000
```

If not set, it defaults to `http://localhost:8000`.

## Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000` (or the next available port).

## Build

Build for production:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Features

- **Run Demo**: Triggers the full multi-agent RFP pipeline
- **RFP Summary**: Displays selected RFP details
- **Agent Timeline**: Visual representation of the agent pipeline
- **Technical Recommendations**: Table showing SKU matching results
- **Pricing**: Detailed line-item pricing with totals
- **JSON Viewer**: Collapsible raw JSON response inspector
- **Review Console**: Human-in-the-loop review interface for overriding SKUs and pricing
  - Override SKU recommendations per line item
  - Adjust global pricing parameters (margin, tax)
  - Recalculate pricing with overrides
  - Save drafts and approve final responses
  - Export approved responses as ZIP files

## Testing Review Flow

1. Start the backend: `python api.py` (from project root)
2. Start the frontend: `npm run dev`
3. Run the pipeline by clicking "Run Demo"
4. Click "Open Review Console" button
5. In the review console:
   - Override SKUs for line items using the dropdown or manual input
   - Adjust margin/tax in the Pricing Overrides panel
   - Click "Recalculate Pricing" to see updated totals
   - Enter reviewer name and click "Save Draft" to save progress
   - Click "Approve Final" to approve and generate export ZIP
   - Download the export ZIP from the success message

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components (Header, Tables, etc.)
│   ├── review/          # Review console components
│   │   ├── ReviewPage.tsx
│   │   ├── ReviewLineItemRow.tsx
│   │   ├── PricingOverridePanel.tsx
│   │   └── ApprovalBar.tsx
│   ├── hooks/           # Custom React hooks
│   ├── types/           # TypeScript type definitions
│   ├── App.tsx          # Main app component with routing
│   ├── main.tsx         # Entry point
│   └── index.css        # Tailwind CSS imports
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

