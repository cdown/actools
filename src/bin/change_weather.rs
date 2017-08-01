use std::fs::File;
use std::fs::OpenOptions;
use std::io::{Read, SeekFrom, Seek, BufWriter, Write};
use std::{io, process, env};

const BUF_SIZE: usize = 128 * 1024;
const WEATHER_LEN_OFFSET: u64 = 12;
const WEATHER_OFFSET: u64 = 16;

struct Args {
    in_fn: String,
    out_fn: String,
    of_weather: String,
}

fn get_existing_weather_len(rp_if: &mut File) -> io::Result<u8> {
    let mut buf = [0; 1];
    rp_if.seek(SeekFrom::Start(WEATHER_LEN_OFFSET))?;
    rp_if.read_exact(&mut buf)?;
    Ok(buf[0])
}

fn copy_exact(
    input: &mut File,
    output: &mut BufWriter<File>,
    start: usize,
    end: usize,
) -> io::Result<usize> {
    let mut buf: Vec<u8> = vec![0; end - start];
    input.seek(SeekFrom::Start(start as u64))?;
    input.read_exact(&mut buf)?;
    Ok(output.write(&buf)?)
}

fn write_header(
    rp_if: &mut File,
    rp_of: &mut BufWriter<File>,
    of_weather: String,
) -> io::Result<()> {
    copy_exact(rp_if, rp_of, 0, WEATHER_LEN_OFFSET as usize)?;
    rp_of.write(&[of_weather.len() as u8])?;
    copy_exact(rp_if, rp_of, WEATHER_LEN_OFFSET as usize + 1, WEATHER_OFFSET as usize)?;
    rp_of.write(of_weather.as_bytes())?;
    Ok(())
}

fn write_frames(mut rp_if: File, mut rp_of: BufWriter<File>, if_weather_len: u8) -> io::Result<()> {
    rp_if.seek(SeekFrom::Start(WEATHER_OFFSET + if_weather_len as u64))?;
    let mut buf = [0; BUF_SIZE];
    let mut done = false;
    while !done {
        let len_read = rp_if.read(&mut buf)?;
        if len_read == 0 {
            done = true;
        }
        rp_of.write_all(&buf[..len_read])?;
    }
    Ok(())
}

fn write_new_replay(
    mut rp_if: File,
    mut rp_of: BufWriter<File>,
    if_weather_len: u8,
    of_weather: String,
) -> io::Result<()> {
    write_header(&mut rp_if, &mut rp_of, of_weather)?;
    write_frames(rp_if, rp_of, if_weather_len)?;
    Ok(())
}

fn parse_args() -> Args {
    let mut args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 3 {
        writeln!(&mut io::stderr(), "Usage: change_weather in out to_weather").expect(
            "Cannot print to stderr",
        );
        process::exit(1);
    }
    Args {
        in_fn: args.remove(0),
        out_fn: args.remove(0),
        of_weather: args.remove(0),
    }
}

fn main() {
    let args = parse_args();

    let mut rp_if = File::open(args.in_fn).expect("Can't open input file");
    let rp_of =
        OpenOptions::new().write(true).truncate(true).create(true).open(args.out_fn).expect(
            "Can't open output file",
        );
    let rp_of = BufWriter::new(rp_of);

    let if_weather_len =
        get_existing_weather_len(&mut rp_if).expect("Can't get existing weather length");

    write_new_replay(rp_if, rp_of, if_weather_len, args.of_weather).expect(
        "Failed to write new replay",
    );
}
