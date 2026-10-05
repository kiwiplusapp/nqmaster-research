//
// BarExporterUTC - writes every bar of the chart (historical + realtime) to a CSV file, timestamps in UTC.
// Use: chart MNQ 12-26 (Tools > Options > Market data > Merge policy = "Merge back adjusted"), 1 Minute,
// Trading hours "CME US Index Futures ETH", Days to load = 1000 (or a custom range from 2020/2024).
// Add this indicator; when the chart finishes loading the file is complete:
//   Documents\NinjaTrader 8\export_<instrument>_<period>.csv
// Format per line: yyyyMMdd HHmmss (bar CLOSE time, UTC);open;high;low;close;volume
//
#region Using declarations
using System;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
	public class BarExporterUTC : Indicator
	{
		private StreamWriter writer;
		private string path;
		private int written;
		private DateTime lastTime = DateTime.MinValue;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Exports all chart bars to CSV (UTC bar-close timestamps) for offline research.";
				Name = "BarExporterUTC";
				Calculate = Calculate.OnBarClose;
				IsOverlay = true;
				DisplayInDataBox = false;
				PaintPriceMarkers = false;
				IsSuspendedWhileInactive = false;
				FileTag = "";
			}
			else if (State == State.DataLoaded)
			{
				string inst = Instrument.FullName.Replace(" ", "_").Replace("/", "-");
				string per = BarsPeriod.Value + BarsPeriod.BarsPeriodType.ToString();
				path = Path.Combine(Core.Globals.UserDataDir, "export_" + inst + "_" + per + (string.IsNullOrEmpty(FileTag) ? "" : "_" + FileTag) + ".csv");
				writer = new StreamWriter(path, false);
				Print("BarExporterUTC | writing " + path);
			}
			else if (State == State.Historical)
			{
			}
			else if (State == State.Realtime)
			{
				if (writer != null) writer.Flush();
				Print(string.Format("BarExporterUTC | historical export done: {0} bars -> {1}", written, path));
			}
			else if (State == State.Terminated)
			{
				if (writer != null)
				{
					writer.Flush(); writer.Close(); writer = null;
					Print(string.Format("BarExporterUTC | closed file ({0} bars): {1}", written, path));
				}
			}
		}

		protected override void OnBarUpdate()
		{
			if (writer == null || Time[0] <= lastTime) return;
			lastTime = Time[0];
			DateTime utc;
			try { utc = TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(Time[0], DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo); }
			catch { utc = Time[0]; }
			writer.WriteLine(string.Format(CultureInfo.InvariantCulture, "{0};{1};{2};{3};{4};{5}",
				utc.ToString("yyyyMMdd HHmmss", CultureInfo.InvariantCulture), Open[0], High[0], Low[0], Close[0], Volume[0]));
			written++;
			if (written % 50000 == 0) writer.Flush();
		}

		[NinjaScriptProperty]
		[Display(Name = "File tag (optional)", Order = 1, GroupName = "Parameters")]
		public string FileTag { get; set; }
	}
}
