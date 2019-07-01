/*
 Navicat Premium Data Transfer

 Source Server         : 10.6
 Source Server Type    : SQL Server
 Source Server Version : 14001000
 Source Host           : 192.168.10.6:1433
 Source Catalog        : a3_new
 Source Schema         : dbo

 Target Server Type    : SQL Server
 Target Server Version : 14001000
 File Encoding         : 65001

 Date: 01/07/2019 13:50:46
*/


-- ----------------------------
-- Table structure for FL_Marks
-- ----------------------------
IF EXISTS (SELECT * FROM sys.all_objects WHERE object_id = OBJECT_ID(N'[dbo].[FL_Marks]') AND type IN ('U'))
	DROP TABLE [dbo].[FL_Marks]
GO

CREATE TABLE [dbo].[FL_Marks] (
  [id] varchar(255) COLLATE Chinese_PRC_CI_AS  NOT NULL,
  [created_at] datetime DEFAULT '' NOT NULL
)
GO

ALTER TABLE [dbo].[FL_Marks] SET (LOCK_ESCALATION = TABLE)
GO


-- ----------------------------
-- Primary Key structure for table FL_Marks
-- ----------------------------
ALTER TABLE [dbo].[FL_Marks] ADD CONSTRAINT [remark] PRIMARY KEY CLUSTERED ([id])
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)  
ON [PRIMARY]
GO

