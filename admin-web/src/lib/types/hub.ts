export type HubUser = {
  id?: string;
  name: string;
  email: string;
  role: string;
  password?: string;
};

export type HubContact = {
  name: string;
  email: string;
  phone: string;
};

export type HubDevice = {
  assignmentId?: number | null;
  hardwareId?: number | null;
  imei: string;
  serialNumber?: string | null;
  model?: string | null;
  hardwareType?: string | null;
  manufacturer?: string | null;
  firmwareVersion?: string | null;
  status?: string | null;
  assetLabel?: string | null;
  assetRegistration?: string | null;
  installationLocation?: string | null;
  technician?: string | null;
  assignedAt?: string | null;
  installedAt?: string | null;
  vehicleId?: string | null;
  vehicleLabel?: string | null;
  sim?: {
    id?: number | null;
    iccid?: string | null;
    msisdn?: string | null;
    carrier?: string | null;
    roamingEnabled?: boolean | null;
    status?: string | null;
  } | null;
  assignmentHistory?: Array<{
    id: number;
    target?: string | null;
    hubId?: string | null;
    hubName?: string | null;
    vehicleId?: string | null;
    vehicleLabel?: string | null;
    technician?: string | null;
    assignedAt?: string | null;
    installedAt?: string | null;
    unassignedAt?: string | null;
    installationLocation?: string | null;
    installationLatitude?: number | null;
    installationLongitude?: number | null;
    assetLabel?: string | null;
    assetRegistration?: string | null;
    notes?: string | null;
    isActive?: boolean;
    simId?: number | null;
    simIccid?: string | null;
    simMsisdn?: string | null;
    simCarrier?: string | null;
    simRoamingEnabled?: boolean;
  }>;
};

export type HubAsset = {
  id: string;
  assetType?: string | null;
  assetName?: string | null;
  assetTypeOther?: string | null;
  registration?: string | null;
  label?: string | null;
  vin?: string | null;
  make?: string | null;
  model?: string | null;
  year?: string | null;
  color?: string | null;
  engineCapacity?: string | null;
  co2Emissions?: string | null;
  fuelType?: string | null;
  status?: string | null;
  notes?: string | null;
  trackingState?: string | null;
  sourceJobId?: string | null;
  assignedDeviceCount: number;
  lastAssignmentAt?: string | null;
};

export type HubAssetDetail = HubAsset & {
  hubId: string;
  hubCode: string;
  hubName: string;
  devices: HubDevice[];
};

export type Hub = {
  id: string;
  name: string;
  code: string;
  type: string;
  tier: string;
  paymentMethod: string;
  billingCycle: string;
  status: string;
  timezone: string;
  country: string;
  city: string;
  address: string;
  goLiveDate: string | null;
  deviceCount: number;
  vehicleCount: number;
  primaryContact: HubContact;
  billingContact: {
    name: string;
    email: string;
    phone?: string;
  };
  notes: string;
  currency: string;
  users: HubUser[];
  devices: HubDevice[];
  subscriptionDaysLeft?: number | null;
  subscriptionStartDate?: string | null;
  subscriptionEndDate?: string | null;
};
