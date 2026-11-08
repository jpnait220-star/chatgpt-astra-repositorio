using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Win32;
namespace DuckPC {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct DisplayMode {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string DeviceName;
        public ushort SpecVersion, DriverVersion, Size, DriverExtra;
        public uint Fields;
        public int PositionX, PositionY;
        public uint DisplayOrientation, DisplayFixedOutput;
        public short Color, Duplex, YResolution, TTOption, Collate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string FormName;
        public ushort LogPixels;
        public uint BitsPerPel, PelsWidth, PelsHeight, DisplayFlags, DisplayFrequency;
        public uint ICMMethod, ICMIntent, MediaType, DitherType, Reserved1, Reserved2, PanningWidth, PanningHeight;
    }
    public static class MonitorInfo {
        [DllImport("user32.dll", EntryPoint="EnumDisplaySettingsW", CharSet=CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool EnumDisplaySettings(string device, int index, ref DisplayMode mode);
        [DllImport("user32.dll", SetLastError=true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool SystemParametersInfo(uint action, uint param, [In] int[] values, uint flags);
        private static DisplayMode NewMode() {
            DisplayMode m = new DisplayMode();
            m.DeviceName = string.Empty; m.FormName = string.Empty;
            m.Size = (ushort)Marshal.SizeOf(typeof(DisplayMode));
            return m;
        }
        public static string Describe(string device) {
            DisplayMode current = NewMode();
            if (!EnumDisplaySettings(device, -1, ref current)) return device + ": leitura indisponivel.";
            SortedSet<uint> rates = new SortedSet<uint>();
            for (int n=0; n<4096; n++) {
                DisplayMode mode = NewMode();
                if (!EnumDisplaySettings(device,n,ref mode)) break;
                if (mode.PelsWidth == current.PelsWidth && mode.PelsHeight == current.PelsHeight && mode.DisplayFrequency>1) rates.Add(mode.DisplayFrequency);
            }
            List<string> list = new List<string>();
            foreach (uint rate in rates) list.Add(rate.ToString());
            string hz = current.DisplayFrequency>1 ? current.DisplayFrequency.ToString() : "nao informado";
            return string.Format("{0}: {1}x{2}, {3} Hz agora.\r\n  Hz anunciados pelo driver nesta resolucao: {4}.\r\n  75 Hz: {5}",device,current.PelsWidth,current.PelsHeight,hz,string.Join(", ",list.ToArray()),rates.Contains(75) ? "disponivel na lista do driver; selecione no Windows." : "nao anunciado nesta resolucao; nao sera forcado.");
        }
        public static bool ApplyMouseRegistry() {
            using (RegistryKey key = Registry.CurrentUser.OpenSubKey(@"Control Panel\Mouse")) {
                if (key == null) return false;
                int[] values = new int[3];
                string[] names = {"MouseThreshold1", "MouseThreshold2", "MouseSpeed"};
                for (int i=0; i<3; i++) {
                    int value;
                    if (!int.TryParse(Convert.ToString(key.GetValue(names[i])),out value)) return false;
                    values[i]=value;
                }
                // Only acceleration/threshold parameters. Never changes click rate,
                // button debounce, pointer speed slider, driver or USB polling rate.
                return SystemParametersInfo(0x0004,0,values,0x0003);
            }
        }
    }
}
