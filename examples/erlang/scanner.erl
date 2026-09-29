-module(scanner).
-export([main/0]).

main() ->
    case os:find_executable("scanimage") of
        false ->
            fail("scanimage was not found; install SANE first");
        Executable ->
            case run(Executable, ["-L"]) of
                {ok, Listing} ->
                    case first_device(Listing) of
                        {ok, Device} -> scan(Executable, Device);
                        error -> fail("No SANE scanner found; check scanimage -L and USB access")
                    end;
                {error, Message} ->
                    fail(Message)
            end
    end.

scan(Executable, Device) ->
    Output = filename:join(["scans", "scanned.png"]),
    case filelib:ensure_dir(Output) of
        ok ->
            case run(Executable, ["--device-name", Device, "--format=png", "--output-file=" ++ Output]) of
                {ok, _} -> io:format("Saved scan to ~s~n", [Output]);
                {error, Message} -> fail(Message)
            end;
        {error, Reason} ->
            fail(io_lib:format("Could not create scans directory: ~p", [Reason]))
    end.

run(Executable, Arguments) ->
    Port = open_port({spawn_executable, Executable}, [binary, exit_status, use_stdio, stderr_to_stdout, {args, Arguments}]),
    collect(Port, []).

collect(Port, Chunks) ->
    receive
        {Port, {data, Data}} -> collect(Port, [Data | Chunks]);
        {Port, {exit_status, 0}} -> {ok, iolist_to_binary(lists:reverse(Chunks))};
        {Port, {exit_status, Status}} ->
            Output = iolist_to_binary(lists:reverse(Chunks)),
            {error, io_lib:format("scanimage exited with status ~B: ~s", [Status, Output])}
    after 180000 ->
        port_close(Port),
        {error, "Scanner timed out after 180 seconds"}
    end.

first_device(Output) ->
    first_device(binary:split(Output, <<"\n">>, [global]), <<"device `">>, <<"' is a">>).

first_device([], _Prefix, _Suffix) -> error;
first_device([Line | Rest], Prefix, Suffix) ->
    case binary:match(Line, Prefix) of
        {Start, PrefixLength} ->
            DeviceStart = Start + PrefixLength,
            Remainder = binary:part(Line, DeviceStart, byte_size(Line) - DeviceStart),
            case binary:match(Remainder, Suffix) of
                {End, _} -> {ok, binary_to_list(binary:part(Remainder, 0, End))};
                nomatch -> first_device(Rest, Prefix, Suffix)
            end;
        nomatch -> first_device(Rest, Prefix, Suffix)
    end.

fail(Message) ->
    io:format(standard_error, "~s~n", [Message]),
    halt(1).