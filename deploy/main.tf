terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.22.0"
    }
  }
}

provider "azurerm" {
  features {}
}
  
resource "azurerm_resource_group" "rg" {
  name     = "nz-census-map"
  location = "ukwest"
}

resource "azurerm_storage_account" "sa" {
  name                     = "stnzcensusmapapi" 
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "plan" {
  name                = "asp-nz-census-map-api"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"   # Y1 = classic Consumption (pay-per-execution)
}

resource "azurerm_linux_function_app" "func" {
  name                       = "func-nz-census-map-api" 
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key

  app_settings = {
    AzureWebJobsFeatureFlags = "EnableWorkerIndexing"
  }

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }
}